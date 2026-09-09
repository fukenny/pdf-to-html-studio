# PDF-to-HTML page for Optimizely/Episerver CMS 12+

This folder is a **drop-in feature package**, not a second website. It adds an authenticated
intranet page where an editor can:

1. Upload a PDF.
2. Convert all pages or a range such as `19-20`.
3. Compare original pages with the HTML preview.
4. Describe a correction and regenerate the HTML/CSS with Gemini.
5. Undo a correction, copy HTML/CSS, or download the initial result as a ZIP.

The browser never receives the Gemini API key. PDF processing and AI calls happen on the server.

## What your Epi developer does

1. Copy the contents of this folder into a feature folder in the CMS solution, preserving the
   `Controllers`, `Models`, `Services`, `Views`, and `wwwroot` structure. A common destination is
   `Features/PdfToHtml` (copy the two static files into the site's `wwwroot/pdf-converter`).
2. Replace `YourSite.Features.PdfToHtml` with the site's namespace.
3. In `Program.cs`, add this line after the CMS services are registered:

   ```csharp
   builder.Services.AddPdfToHtmlConverter(builder.Configuration);
   ```

4. Copy the `PdfConverter` section from `appsettings.sample.json` into the site's configuration.
   Set `ConverterProjectPath` to the deployed Python converter folder and `PythonExecutable` to
   that folder's virtual-environment Python.
5. Copy this repository's `src`, `pyproject.toml`, and `README.md` to the folder named by
   `ConverterProjectPath`, then install the converter once on the web server:

   ```bash
   cd "/path/to/PDF to HTML"
   python3 -m venv .venv
   .venv/bin/pip install -e .
   ```

6. Put the Gemini key in a server secret or environment variable, **not** in source control:

   ```text
   PdfConverter__GeminiApiKey=YOUR_KEY
   ```

   Gemini is optional. Basic conversion works without it; the “Regenerate with Gemini” button
   reports that it is not configured. Gemini API usage can incur charges depending on the model,
   account, and current Google pricing.
7. Update the `Layout` path at the top of `Views/Index.cshtml` to use the site's normal page layout.
8. Build the CMS. In edit mode, create a page using the new **PDF to HTML converter** page type.
   Restrict that page to the communications/web-team group.

## Test before production

- Upload a representative PDF and enter a small page range such as `1-2`.
- Confirm that both original previews appear and that the generated HTML preview loads.
- Try feedback such as: “Balance the title and line up the legend dot, percentage, and label.”
- Copy the HTML and CSS into a test Epi content block and check desktop and mobile layouts.
- For results that include visual-reference images, use **Download ZIP**, upload the files under
  `assets/pages` to Epi's media library, and replace those relative image paths before publishing.
  The one-click HTML copy is best for output whose infographics have already been rebuilt in HTML/CSS.

## Important first-release boundaries

- The free local pass extracts text and retains every selected page as a visual reference. It does
  not automatically reconstruct every infographic as editable bars and donut charts.
- Gemini refinement operates on generated code and editor feedback. A production phase should also
  send selected page images to Gemini so it can interpret complex infographics directly.
- Generated output still needs a human review for data accuracy, reading order, accessibility, and
  CMS theme collisions before publication.
- Jobs are tracked in memory and stored under `App_Data`. Add scheduled deletion (for example after
  24 hours), malware scanning, logging, and your organization's retention rules before launch.
- If your site is CMS 11 / .NET Framework rather than CMS 12+, the content type can be reused but
  the ASP.NET Core controller, DI, and upload code must be adapted.

## Why this architecture

The page belongs in the intranet because it gives staff one consistent, access-controlled workflow.
The conversion engine remains a local server component, so ordinary users install nothing and the
Gemini credential stays protected. HTML and CSS are outputs that editors review and publish; the
uploaded PDF is not sent to Gemini in this first package.
