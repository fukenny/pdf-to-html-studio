# PDF to HTML Studio

A working proof of concept for converting selected PDF pages into accessible, CMS-safe HTML and
CSS. The project includes a local browser application, an Epi front-end mockup, and a CMS 12
integration starter.

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

## How it works

1. **The editor uploads a PDF.** The browser sends the file and optional page range to the local
   Python server. The PDF is not sent to Gemini during this first conversion.
2. **The backend reads and renders the selected pages.** It validates the PDF, extracts available
   text and basic document structure, and renders page images for side-by-side comparison.
3. **The converter creates CMS-safe output.** It returns one HTML section with the wrapper
   `#pdf-html-content` and one scoped `<style>` block. It does not return a complete web page with
   `<html>`, `<head>`, `<body>`, or `<main>` elements.
4. **The editor reviews the result.** The Studio displays the original page and the generated HTML
   next to each other. HTML and CSS can be edited directly, copied, or downloaded.
5. **Gemini can perform a correction pass.** When the editor clicks **Apply with Gemini**, the
   backend sends the current HTML, CSS, written feedback, and an optional screenshot to Gemini.
   Gemini returns revised HTML and CSS in a structured response.
6. **The backend validates the response.** It rejects scripts, forms, iframes, event handlers,
   unsafe references, and output that does not use the required wrapper. The editor then reviews
   the updated preview before copying anything into Epi.
7. **The approved result is pasted into Epi.** The HTML section goes into the WYSIWYG/source block,
   and the `<style>` block goes into the permitted code or HTML block. No standalone page shell is
   included.

### Backend talking points

- **The browser is the workbench; the backend does the conversion.** A WYSIWYG block cannot safely
  open PDFs, run Python, or protect an API key, so those responsibilities stay on the server.
- **The default conversion is local.** PDF validation, text extraction, page rendering, and initial
  HTML generation run without an AI service or per-document API charge.
- **Gemini is a review assistant, not the source of truth.** It helps translate visual feedback into
  HTML/CSS changes, while the original PDF and a human reviewer remain authoritative.
- **Visual feedback closes an important gap.** An optional screenshot lets Gemini see how Epi's own
  theme and margins affect the applied code, not merely read the code in isolation.
- **The API key never belongs in Epi or front-end JavaScript.** It is read from a server-side
  environment variable and is excluded from Git.
- **The output is deliberately isolated.** Scoped selectors reduce the risk of changing Epi's
  navigation, headers, or unrelated page content.
- **Every generated result remains reviewable.** Editors can compare source and result, inspect the
  code, undo a correction, and verify facts and accessibility before publishing.
- **Production hardening is straightforward.** The same backend can later run behind authenticated
  Epi endpoints with upload limits, malware scanning, automatic file cleanup, logging, and the
  organization's retention controls.

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

### Windows instructions — not yet tested

The conversion code is designed to be cross-platform, but the following Windows setup has **not
yet been tested on a Windows computer**. Use PowerShell and install Python 3.11 or newer first.

```powershell
cd "C:\path\to\pdf-to-html-studio"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python .\local-app\server.py
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765) in a browser.

To enable Gemini for the current PowerShell session:

```powershell
$env:GEMINI_API_KEY = Read-Host "Gemini API key"
python .\local-app\server.py
```

Do not put the API key in the repository or front-end code. The macOS `.command` launchers do not
run on Windows. A tested Windows launcher should be added before a production rollout.

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
is never added to the page or repository. This proof of concept sends generated HTML, CSS, editor
feedback, and an optional editor-selected screenshot to Gemini; it does not send the original PDF.

## Epi demonstration files

The `epi-prototype` folder contains the presentation-only front end:

- `epi-prototype/html-block.html` — paste into an Epi HTML/WYSIWYG block in source mode.
- `epi-prototype/css-code-block.css` — paste into the page CSS/code block.

Those Epi controls are intentionally a visual mockup. Use the local app to demonstrate real PDF
conversion. After approval, `epi-app` contains the CMS 12 server integration starter that connects
the interface to the converter.

## Repository map

```text
local-app/          Working local browser application
src/pdf2html/       Python conversion engine and command-line tool
epi-prototype/      Copy-ready Epi HTML and CSS mockup
epi-app/            Optimizely/Episerver CMS 12 integration starter
tests/              Automated output checks
```

## Privacy and production notes

Local conversion keeps the PDF on the computer. Before production, add authentication, antivirus
scanning, automatic job cleanup, organizational retention rules, audit logging, and accessibility
review. Generated facts and chart labels must be checked against the source PDF before publishing.
