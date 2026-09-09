from __future__ import annotations

import json
from pathlib import Path

from .extract import extract_document, render_pages
from .html import STYLES, render_html
from .model import ConversionResult


def _parse_pages(value: str | None, page_count: int) -> list[int]:
    if not value:
        return list(range(1, page_count + 1))
    selected: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ValueError(f"Invalid page range: {part}")
            selected.update(range(start, end + 1))
        else:
            selected.add(int(part))
    if not selected or min(selected) < 1 or max(selected) > page_count:
        raise ValueError(f"Pages must be between 1 and {page_count}")
    return sorted(selected)


def convert(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 144,
    pages: str | None = None,
) -> ConversionResult:
    pdf_path = pdf_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a readable PDF: {pdf_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = output_dir / "assets" / "pages"
    from .extract import inspect_pdf

    _, source_page_count = inspect_pdf(pdf_path)
    selected_pages = _parse_pages(pages, source_page_count)
    rendered_pages = render_pages(pdf_path, pages_dir, dpi=dpi, page_numbers=selected_pages)
    document = extract_document(pdf_path, rendered_pages, page_numbers=selected_pages)
    if len(rendered_pages) != len(document.pages):
        raise RuntimeError("Rendered page count does not match the selected page count")

    document_path = output_dir / "document.json"
    html_path = output_dir / "index.html"
    report_path = output_dir / "report.json"
    ocr_candidates = [page.number for page in document.pages if page.needs_ocr]
    document_path.write_text(json.dumps(document.to_dict(), indent=2), encoding="utf-8")
    html_path.write_text(render_html(document), encoding="utf-8")
    (output_dir / "styles.css").write_text(STYLES, encoding="utf-8")
    (output_dir / "styles-for-epi.html").write_text(
        f'<style id="pdf-html-styles">\n{STYLES}</style>\n', encoding="utf-8"
    )
    report = {
        "source": document.source_name,
        "pages_processed": len(document.pages),
        "source_page_count": source_page_count,
        "selected_pages": selected_pages,
        "rendered_pages": len(rendered_pages),
        "ocr_candidate_pages": ocr_candidates,
        "text_blocks": sum(len(page.blocks) for page in document.pages),
        "visual_fallback_coverage": "100%",
        "status": "review_required" if ocr_candidates else "converted",
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return ConversionResult(output_dir, html_path, document_path, report_path, len(document.pages), ocr_candidates)
