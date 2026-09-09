# Epi presentation mockup

This is the visual front end for the proposed intranet tool.

1. Paste `html-block.html` into a WYSIWYG/HTML block using source-code mode.
2. Paste `css-code-block.css` into the page CSS/code block.
3. Publish the test page.

The buttons are intentionally non-functional in Epi today. Run the local application for the live,
working conversion. After approval, the backend endpoints in `epi-app` connect this same experience
to the real converter.

If Epi removes input, textarea, or button elements, a developer must allow those elements or render
the interface from a custom block. The CSS is fully scoped under `.pdf-converter-mock` and does not
style the intranet page around it.
