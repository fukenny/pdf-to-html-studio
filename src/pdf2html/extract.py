from __future__ import annotations

import statistics
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium
from pypdf import PdfReader

from .model import Document, Page, TextBlock


def inspect_pdf(path: Path) -> tuple[dict[str, str], int]:
    reader = PdfReader(path)
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError("Password-protected PDFs are not supported yet") from exc
    metadata = {str(k).lstrip("/"): str(v) for k, v in (reader.metadata or {}).items() if v}
    return metadata, len(reader.pages)


def render_pages(
    pdf_path: Path,
    pages_dir: Path,
    dpi: int = 144,
    page_numbers: list[int] | None = None,
) -> list[Path]:
    pages_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    try:
        document = pdfium.PdfDocument(pdf_path)
        indexes = [number - 1 for number in page_numbers] if page_numbers else range(len(document))
        for index in indexes:
            page = document[index]
            bitmap = page.render(scale=dpi / 72, rev_byteorder=True)
            destination = pages_dir / f"page-{index + 1:04d}.png"
            bitmap.to_pil().save(destination, "PNG", optimize=True)
            rendered.append(destination)
            bitmap.close()
            page.close()
        document.close()
    except Exception as exc:
        raise RuntimeError(f"PDF rendering failed: {exc}") from exc
    return rendered


def _classify_blocks(raw_blocks: list[dict]) -> list[TextBlock]:
    sizes = [float(b.get("size", 0)) for b in raw_blocks if b.get("text", "").strip()]
    median_size = statistics.median(sizes) if sizes else 0
    blocks: list[TextBlock] = []
    for raw in raw_blocks:
        text = " ".join(str(raw.get("text", "")).split())
        if not text:
            continue
        size = float(raw.get("size", median_size))
        kind = "paragraph"
        level = None
        if median_size and size >= median_size * 1.45 and len(text) < 160:
            kind, level = "heading", 2
        elif median_size and size >= median_size * 1.2 and len(text) < 160:
            kind, level = "heading", 3
        blocks.append(
            TextBlock(
                text=text,
                bbox=(float(raw["x0"]), float(raw["top"]), float(raw["x1"]), float(raw["bottom"])),
                kind=kind,
                level=level,
            )
        )
    return blocks


def extract_document(
    pdf_path: Path,
    rendered_pages: list[Path],
    page_numbers: list[int] | None = None,
) -> Document:
    metadata, page_count = inspect_pdf(pdf_path)
    pages: list[Page] = []
    with pdfplumber.open(pdf_path) as pdf:
        numbers = page_numbers or list(range(1, len(pdf.pages) + 1))
        for rendered_index, page_number in enumerate(numbers):
            pdf_page = pdf.pages[page_number - 1]
            words = pdf_page.extract_words(extra_attrs=["size"])
            # Group words into lines while retaining a conservative reading order.
            lines: dict[int, list[dict]] = {}
            for word in words:
                line_key = round(float(word["top"]) / 3)
                lines.setdefault(line_key, []).append(word)
            raw_blocks = []
            for line_words in sorted(lines.values(), key=lambda ws: min(float(w["top"]) for w in ws)):
                line_words.sort(key=lambda word: float(word["x0"]))
                raw_blocks.append(
                    {
                        "text": " ".join(str(word["text"]) for word in line_words),
                        "x0": min(float(word["x0"]) for word in line_words),
                        "top": min(float(word["top"]) for word in line_words),
                        "x1": max(float(word["x1"]) for word in line_words),
                        "bottom": max(float(word["bottom"]) for word in line_words),
                        "size": statistics.median(float(word.get("size", 0)) for word in line_words),
                    }
                )
            blocks = _classify_blocks(raw_blocks)
            character_count = sum(len(block.text) for block in blocks)
            image = rendered_pages[rendered_index].relative_to(
                rendered_pages[rendered_index].parents[2]
            ).as_posix()
            pages.append(
                Page(
                    number=page_number,
                    width=float(pdf_page.width),
                    height=float(pdf_page.height),
                    image=image,
                    blocks=blocks,
                    needs_ocr=character_count < 40,
                )
            )
    title = metadata.get("Title") or pdf_path.stem.replace("_", " ").replace("-", " ").strip()
    return Document(pdf_path.name, title, page_count, pages, metadata)
