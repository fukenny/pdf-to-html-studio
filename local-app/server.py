#!/usr/bin/env python3
from __future__ import annotations

import base64
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from email import policy
from email.parser import BytesParser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"
WORK = Path(tempfile.gettempdir()) / "pdf-to-html-demo"
MAX_UPLOAD = 50 * 1024 * 1024
sys.path.insert(0, str(PROJECT / "src"))

from pdf2html.converter import convert  # noqa: E402


def _json_bytes(value: object) -> bytes:
    return json.dumps(value).encode("utf-8")


class DemoHandler(SimpleHTTPRequestHandler):
    server_version = "PdfToHtmlDemo/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def send_json(self, value: object, status: int = 200) -> None:
        body = _json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.startswith("/jobs/"):
            return self.serve_job_file()
        if self.path == "/health":
            return self.send_json({"status": "ok"})
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        try:
            if self.path == "/api/convert":
                return self.convert_pdf()
            if self.path == "/api/refine":
                return self.refine_with_gemini()
            self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, RuntimeError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self.log_error("Unhandled request error: %r", exc)
            self.send_json({"error": "The request could not be completed."}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_UPLOAD:
            raise ValueError("The upload must be a PDF smaller than 50 MB.")
        return self.rfile.read(length)

    def multipart(self) -> dict[str, tuple[str | None, bytes]]:
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            raise ValueError("Expected a PDF upload.")
        envelope = (
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode()
            + self.read_body()
        )
        message = BytesParser(policy=policy.default).parsebytes(envelope)
        fields: dict[str, tuple[str | None, bytes]] = {}
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if name:
                fields[name] = (part.get_filename(), part.get_payload(decode=True) or b"")
        return fields

    def convert_pdf(self) -> None:
        fields = self.multipart()
        filename, pdf = fields.get("pdf", (None, b""))
        pages = fields.get("pages", (None, b""))[1].decode("utf-8", "replace").strip() or None
        if not filename or not filename.lower().endswith(".pdf") or not pdf.startswith(b"%PDF-"):
            raise ValueError("Choose a valid PDF file.")
        if pages and not re.fullmatch(r"[0-9, -]+", pages):
            raise ValueError("Pages must look like 19-20 or 1,3,7.")

        job_id = uuid.uuid4().hex
        job = WORK / job_id
        output = job / "output"
        job.mkdir(parents=True)
        input_path = job / "input.pdf"
        input_path.write_bytes(pdf)
        result = convert(input_path, output, pages=pages)
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        selected = report["selected_pages"]
        html = result.html_path.read_text(encoding="utf-8")
        raw_css = (output / "styles.css").read_text(encoding="utf-8")
        css = f'<style id="pdf-html-styles">\n{raw_css}</style>'
        for number in selected:
            html = html.replace(
                f"assets/pages/page-{number:04d}.png",
                f"/jobs/{job_id}/assets/pages/page-{number:04d}.png",
            )
        self.send_json({
            "jobId": job_id,
            "fileName": Path(filename).name,
            "html": html,
            "css": css,
            "qualityMode": "basic-extraction",
            "pages": [
                {"number": number, "imageUrl": f"/jobs/{job_id}/assets/pages/page-{number:04d}.png"}
                for number in selected
            ],
            "report": report,
        })

    def refine_with_gemini(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("Gemini is not configured. You can still edit the HTML and CSS directly.")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 8_000_000:
            raise ValueError("The correction request is too large.")
        request_data = json.loads(self.rfile.read(length))
        feedback = str(request_data.get("feedback", ""))[:4000]
        html = str(request_data.get("html", ""))[:300_000]
        css = str(request_data.get("css", ""))[:150_000]
        image = request_data.get("image")
        if not feedback:
            raise ValueError("Describe what should change first.")
        prompt = f"""Refine this accessible PDF-to-HTML section using the editor feedback.
Preserve every fact and number. Return JSON with html, css, and summary. HTML must be a fragment
        wrapped in <section id="pdf-html-content" class="pdf-html">. Return CSS inside one
        <style id="pdf-html-styles"> tag, with every rule scoped below .pdf-html. Never return
        scripts, forms, iframes, event attributes, remote resources, or invented information.

EDITOR FEEDBACK:\n{feedback}\n\nCURRENT HTML:\n{html}\n\nCURRENT CSS:\n{css}"""
        parts: list[dict[str, object]] = [{"text": prompt}]
        if image:
            mime_type = str(image.get("mimeType", ""))
            image_data = str(image.get("data", ""))
            if mime_type not in {"image/png", "image/jpeg", "image/webp"}:
                raise ValueError("The screenshot must be a PNG, JPEG, or WebP image.")
            try:
                decoded = base64.b64decode(image_data, validate=True)
            except (ValueError, TypeError) as exc:
                raise ValueError("The screenshot data was invalid.") from exc
            if len(decoded) > 5 * 1024 * 1024:
                raise ValueError("The screenshot must be smaller than 5 MB.")
            prompt += (
                "\n\nThe attached screenshot shows how the current code actually renders. "
                "Use it as visual evidence when applying the editor's correction."
            )
            parts = [{"text": prompt}, {"inline_data": {"mime_type": mime_type, "data": image_data}}]
        payload = _json_bytes({
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "html": {"type": "STRING"},
                        "css": {"type": "STRING"},
                        "summary": {"type": "STRING"},
                    },
                    "required": ["html", "css", "summary"],
                },
            },
        })
        preferred = os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")
        models = list(dict.fromkeys([preferred, "gemini-3.6-flash", "gemini-3.5-flash"]))
        response_body = None
        last_status = 503
        for attempt, model in enumerate(models):
            api_request = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                data=payload,
                headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                method="POST",
            )
            try:
                with urllib.request.urlopen(api_request, timeout=90) as response:
                    response_body = json.load(response)
                break
            except urllib.error.HTTPError as exc:
                last_status = exc.code
                if exc.code not in (404, 429, 500, 502, 503, 504):
                    raise ValueError(f"Gemini rejected the correction (HTTP {exc.code}).") from exc
                if attempt < len(models) - 1:
                    time.sleep(attempt + 1)
        if response_body is None:
            raise ValueError(
                f"Gemini is temporarily unavailable (HTTP {last_status}). Please try again in a minute."
            )
        text = response_body["candidates"][0]["content"]["parts"][0]["text"]
        refined = json.loads(text)
        refined_css = str(refined.get("css", "")).strip()
        if not refined_css.lower().startswith("<style"):
            refined["css"] = f'<style id="pdf-html-styles">\n{refined_css}\n</style>'
        combined = refined.get("html", "") + refined.get("css", "")
        if re.search(r"<(script|iframe|object|embed|form)\b|\son\w+\s*=|javascript:", combined, re.I):
            raise ValueError("Gemini returned unsafe code, so the change was rejected.")
        if not re.match(r'^\s*<section\s+id=["\']pdf-html-content["\']', refined.get("html", ""), re.I):
            raise ValueError("Gemini did not return the required Epi section wrapper.")
        self.send_json(refined)

    def serve_job_file(self) -> None:
        match = re.fullmatch(r"/jobs/([a-f0-9]{32})/(assets/pages/page-\d{4}\.png|export\.zip)", self.path)
        if not match:
            return self.send_error(HTTPStatus.NOT_FOUND)
        job_id, relative = match.groups()
        output = WORK / job_id / "output"
        if relative == "export.zip":
            memory = io.BytesIO()
            with zipfile.ZipFile(memory, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in output.rglob("*"):
                    if path.is_file():
                        archive.write(path, path.relative_to(output))
            body = memory.getvalue()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="pdf-html-package.zip"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        path = output / relative
        if not path.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND)
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get("PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), DemoHandler)
    print(f"PDF to HTML demo running at http://127.0.0.1:{port}", flush=True)
    print("Press Control-C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
