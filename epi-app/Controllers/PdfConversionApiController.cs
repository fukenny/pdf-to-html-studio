using System.IO.Compression;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace YourSite.Features.PdfToHtml;

[ApiController]
[Authorize]
[AutoValidateAntiforgeryToken]
[Route("api/pdf-converter")]
public sealed class PdfConversionApiController : ControllerBase
{
    private readonly IPdfConversionService _converter;
    private readonly IGeminiRefinementService _gemini;
    private readonly ConversionJobStore _jobs;

    public PdfConversionApiController(
        IPdfConversionService converter,
        IGeminiRefinementService gemini,
        ConversionJobStore jobs)
    {
        _converter = converter;
        _gemini = gemini;
        _jobs = jobs;
    }

    [HttpPost("convert")]
    [RequestFormLimits(MultipartBodyLengthLimit = 52_428_800)]
    public async Task<ActionResult<ConversionResponse>> Convert(
        [FromForm] IFormFile pdf,
        [FromForm] string? pages,
        CancellationToken cancellationToken)
    {
        try { return Ok(await _converter.ConvertAsync(pdf, pages, cancellationToken)); }
        catch (InvalidOperationException exception) { return BadRequest(new { error = exception.Message }); }
    }

    [HttpPost("refine")]
    public async Task<ActionResult<RefineResponse>> Refine(
        RefineRequest request,
        CancellationToken cancellationToken)
    {
        try
        {
            if (!_jobs.TryGet(request.JobId, out var job)) return NotFound(new { error = "Conversion job not found." });
            var result = await _gemini.RefineAsync(request, cancellationToken);
            var output = Path.Combine(job.Directory, "output");
            await System.IO.File.WriteAllTextAsync(Path.Combine(output, "index.html"), result.Html, cancellationToken);
            await System.IO.File.WriteAllTextAsync(Path.Combine(output, "styles-for-epi.html"), result.Css, cancellationToken);
            var rawCss = System.Text.RegularExpressions.Regex.Replace(
                result.Css, @"^\s*<style[^>]*>|</style>\s*$", "", System.Text.RegularExpressions.RegexOptions.IgnoreCase);
            await System.IO.File.WriteAllTextAsync(Path.Combine(output, "styles.css"), rawCss, cancellationToken);
            return Ok(result);
        }
        catch (InvalidOperationException exception) { return BadRequest(new { error = exception.Message }); }
    }

    [HttpGet("jobs/{jobId}/assets/pages/{fileName}")]
    [IgnoreAntiforgeryToken]
    public IActionResult Asset(string jobId, string fileName)
    {
        if (!_jobs.TryGet(jobId, out var job) || !System.Text.RegularExpressions.Regex.IsMatch(fileName, @"^page-\d{4}\.png$"))
            return NotFound();
        var path = Path.Combine(job.Directory, "output", "assets", "pages", fileName);
        return System.IO.File.Exists(path) ? PhysicalFile(path, "image/png") : NotFound();
    }

    [HttpGet("jobs/{jobId}/export")]
    [IgnoreAntiforgeryToken]
    public IActionResult Export(string jobId)
    {
        if (!_jobs.TryGet(jobId, out var job)) return NotFound();
        var output = Path.Combine(job.Directory, "output");
        if (!Directory.Exists(output)) return NotFound();
        var stream = new MemoryStream();
        using (var archive = new ZipArchive(stream, ZipArchiveMode.Create, true))
        {
            foreach (var path in Directory.EnumerateFiles(output, "*", SearchOption.AllDirectories))
            {
                var name = Path.GetRelativePath(output, path).Replace('\\', '/');
                archive.CreateEntryFromFile(path, name);
            }
        }
        stream.Position = 0;
        return File(stream, "application/zip", "pdf-html-package.zip");
    }
}
