# PDF to HTML Studio

A working proof of concept for converting selected PDF pages into accessible, CMS-safe HTML and
CSS. The project includes a local browser application, an infographic-heavy acceptance example,
an Epi front-end mockup, and a CMS 12 integration starter.

## What works today

- Upload a PDF through a local browser page.
- Convert all pages or a range such as `19-20`.
- Extract native text and approximate heading structure.
- Render every selected page so visual information is never silently discarded.
- Compare the original PDF pages and generated HTML side by side.
- Edit generated HTML or CSS and immediately refresh the preview.
- Copy HTML/CSS or download the conversion files as a ZIP.
- Optionally refine the result using plain-language feedback and the Gemini API.
- Keep generated CSS inside `.pdf-html` so it does not restyle the surrounding CMS page.

## Run the live demonstration

Requires Python 3.11 or newer.

### macOS: easiest method

Double-click `start-demo.command`. The first run creates the local environment and installs the
required packages. Then open [http://127.0.0.1:8765](http://127.0.0.1:8765).

### Terminal method

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python local-app/server.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765), choose a PDF, enter `19-20`, and select
**Convert PDF**.

### Optional Gemini corrections

Basic conversion is free and local. On macOS, double-click `configure-gemini.command`, paste a new
API key when prompted, and then restart `start-demo.command`. The key is stored only in the local
`.env` file, which is excluded from Git.

Alternatively, set an API key in Terminal before starting the server:

```bash
export GEMINI_API_KEY="your-key"
python local-app/server.py
```

Gemini is optional and may incur Google API charges. The key stays in the local/server process and
is never added to the page or repository. This proof of concept sends generated HTML, CSS, and
editor feedback to Gemini; it does not send the original PDF.

## Epi demonstration files

The `epi-prototype` folder contains the presentation-only front end:

- `epi-prototype/html-block.html` — paste into an Epi HTML/WYSIWYG block in source mode.
- `epi-prototype/css-code-block.css` — paste into the page CSS/code block.

Those Epi controls are intentionally a visual mockup. Use the local app to demonstrate real PDF
conversion. After approval, `epi-app` contains the CMS 12 server integration starter that connects
the interface to the converter.

## Acceptance example: pages 19–20

`demo/pages-19-20` is a deliberately handcrafted semantic recreation of the most difficult pages
in the Success 2029 report. It demonstrates the target quality for infographic conversions:

- responsive metric cards;
- CSS-rendered donut and bar charts;
- accessible chart descriptions and a graduation-rate data table;
- semantic headings, lists, and definition lists; and
- layouts that collapse cleanly on narrow screens.

The generic converter preserves complex infographics as page references but does not yet rebuild
every unfamiliar chart as editable HTML. That requires visual interpretation, validation, and a
human review loop. The handcrafted pages prove the output is possible; the local app proves the
conversion and review workflow.

## Repository map

```text
local-app/          Working local browser application
src/pdf2html/       Python conversion engine and command-line tool
demo/pages-19-20/  High-quality infographic acceptance example
epi-prototype/      Copy-ready Epi HTML and CSS mockup
epi-app/            Optimizely/Episerver CMS 12 integration starter
tests/              Automated output checks
```

## Privacy and production notes

Local conversion keeps the PDF on the computer. Before production, add authentication, antivirus
scanning, automatic job cleanup, organizational retention rules, audit logging, and accessibility
review. Generated facts and chart labels must be checked against the source PDF before publishing.
