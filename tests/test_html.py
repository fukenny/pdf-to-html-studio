from pdf2html.html import render_html
from pdf2html.model import Document, Page, TextBlock


def test_html_is_semantic_and_escapes_content():
    document = Document(
        source_name="sample.pdf",
        title="A & B",
        page_count=1,
        pages=[
            Page(
                number=1,
                width=612,
                height=792,
                image="assets/pages/page-1.png",
                blocks=[TextBlock("Revenue < Costs", (10, 10, 100, 20), "heading", 2)],
            )
        ],
    )
    result = render_html(document)
    assert "<h1>" not in result
    assert "A &amp; B" not in result
    assert "<h2>Revenue &lt; Costs</h2>" in result
    assert result.startswith('<section id="pdf-html-content" class="pdf-html"')
    assert "<html>" not in result and "<html " not in result
    assert "<head>" not in result and "<head " not in result
    assert "<body>" not in result and "<body " not in result
    assert "<main>" not in result and "<main " not in result
    assert 'id="page-1"' in result
    assert "View original page layout" in result


def test_ocr_warning_is_exposed():
    document = Document(
        source_name="scan.pdf",
        title="Scan",
        page_count=1,
        pages=[Page(1, 612, 792, "assets/pages/page-1.png", needs_ocr=True)],
    )
    assert "may require OCR" in render_html(document)
