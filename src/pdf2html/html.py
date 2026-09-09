from __future__ import annotations

import html

from .model import Document


STYLES = """\
.pdf-html { color-scheme: light; --ink: #17202a; --muted: #5d6d7e; --paper: #fff; --bg: #eef2f5; width: min(78rem, 100%); margin: 0 auto; padding: 2rem 1rem 5rem; background: var(--bg); color: var(--ink); font: 17px/1.6 system-ui, sans-serif; }
.pdf-html, .pdf-html * { box-sizing: border-box; }
.pdf-html :where(h1,h2,h3,p,figure) { margin-block-start: 0; }
.pdf-html .page { background: var(--paper); padding: clamp(1rem, 4vw, 3rem); margin: 0 0 1.5rem; }
.pdf-html .page-label { color: var(--muted); font-size: .85rem; letter-spacing: .08em; text-transform: uppercase; }
.pdf-html .content { max-width: 72ch; }
.pdf-html .visual-reference { margin-top: 2rem; border-top: 1px solid #d9e0e5; padding-top: 1rem; }
.pdf-html .visual-reference img { display: block; width: 100%; height: auto; margin-top: 1rem; border: 1px solid #ccd5dc; }
.pdf-html .warning { padding: .75rem 1rem; border-left: .3rem solid #b66a00; background: #fff4df; }
@media print { .pdf-html { background: white; } .pdf-html .page { break-after: page; } }
"""


def render_html(document: Document) -> str:
    sections: list[str] = []
    for page in document.pages:
        body: list[str] = []
        if page.needs_ocr:
            body.append('<p class="warning">This page may require OCR. Use the visual reference below.</p>')
        for block in page.blocks:
            escaped = html.escape(block.text)
            if block.kind == "heading":
                level = block.level or 2
                body.append(f"<h{level}>{escaped}</h{level}>")
            else:
                body.append(f"<p>{escaped}</p>")
        image = html.escape(page.image, quote=True)
        sections.append(
            f'''<section class="page" id="page-{page.number}" aria-labelledby="page-label-{page.number}">
  <div class="page-label" id="page-label-{page.number}">Page {page.number}</div>
  <div class="content">{"".join(body)}</div>
  <details class="visual-reference">
    <summary>View original page layout</summary>
    <img src="{image}" alt="Visual reference for PDF page {page.number}" loading="lazy">
  </details>
</section>'''
        )
    return f'''<section id="pdf-html-content" class="pdf-html" aria-label="Converted PDF content">
  {"".join(sections)}
</section>
'''
