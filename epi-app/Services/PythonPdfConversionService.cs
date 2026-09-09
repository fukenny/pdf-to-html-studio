using System.Diagnostics;
using System.Text.Json;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Options;

namespace YourSite.Features.PdfToHtml;

public interface IPdfConversionService
{
    Task<ConversionResponse> ConvertAsync(IFormFile pdf, string? pages, CancellationToken cancellationToken);
}

public sealed class PythonPdfConversionService : IPdfConversionService
{
    private readonly PdfConverterOptions _options;
    private readonly ConversionJobStore _jobs;
    private readonly IWebHostEnvironment _environment;

    public PythonPdfConversionService(
        IOptions<PdfConverterOptions> options,
        ConversionJobStore jobs,
        IWebHostEnvironment environment)
    {
        _options = options.Value;
        _jobs = jobs;
        _environment = environment;
    }

    public async Task<ConversionResponse> ConvertAsync(
        IFormFile pdf,
        string? pages,
        CancellationToken cancellationToken)
    {
        if (pdf.Length is <= 0 || pdf.Length > _options.MaxUploadBytes)
            throw new InvalidOperationException("Choose a PDF smaller than the configured upload limit.");

        var workRoot = Path.IsPathRooted(_options.WorkPath)
            ? _options.WorkPath
            : Path.Combine(_environment.ContentRootPath, _options.WorkPath);
        Directory.CreateDirectory(workRoot);
        var jobDirectory = Path.Combine(workRoot, Guid.NewGuid().ToString("N"));
        var outputDirectory = Path.Combine(jobDirectory, "output");
        Directory.CreateDirectory(jobDirectory);
        var inputPath = Path.Combine(jobDirectory, "input.pdf");

        await using (var target = File.Create(inputPath))
            await pdf.CopyToAsync(target, cancellationToken);

        await using (var check = File.OpenRead(inputPath))
        {
            var signature = new byte[5];
            if (await check.ReadAsync(signature, cancellationToken) != 5 ||
                System.Text.Encoding.ASCII.GetString(signature) != "%PDF-")
                throw new InvalidOperationException("The uploaded file is not a valid PDF.");
        }

        var start = new ProcessStartInfo
        {
            FileName = _options.PythonExecutable,
            WorkingDirectory = _options.ConverterProjectPath,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        start.Environment["PYTHONPATH"] = Path.Combine(_options.ConverterProjectPath, "src");
        start.ArgumentList.Add("-m");
        start.ArgumentList.Add("pdf2html");
        start.ArgumentList.Add(inputPath);
        start.ArgumentList.Add("--output");
        start.ArgumentList.Add(outputDirectory);
        if (!string.IsNullOrWhiteSpace(pages))
        {
            start.ArgumentList.Add("--pages");
            start.ArgumentList.Add(pages.Trim());
        }

        using var process = Process.Start(start) ?? throw new InvalidOperationException("Could not start converter.");
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(_options.TimeoutSeconds));
        try { await process.WaitForExitAsync(timeout.Token); }
        catch (OperationCanceledException)
        {
            try { process.Kill(true); } catch { /* process may already have exited */ }
            throw new InvalidOperationException("Conversion timed out. Try fewer pages.");
        }
        var error = await process.StandardError.ReadToEndAsync(cancellationToken);
        if (process.ExitCode != 0)
            throw new InvalidOperationException(string.IsNullOrWhiteSpace(error) ? "Conversion failed." : error.Trim());

        var job = _jobs.Add(jobDirectory);
        var html = await File.ReadAllTextAsync(Path.Combine(outputDirectory, "index.html"), cancellationToken);
        var rawCss = await File.ReadAllTextAsync(Path.Combine(outputDirectory, "styles.css"), cancellationToken);
        var css = $"<style id=\"pdf-html-styles\">\n{rawCss}</style>";
        using var reportDocument = JsonDocument.Parse(
            await File.ReadAllTextAsync(Path.Combine(outputDirectory, "report.json"), cancellationToken));
        var report = reportDocument.RootElement;
        var selectedPages = report.GetProperty("selected_pages").EnumerateArray().Select(x => x.GetInt32()).ToArray();
        var ocrPages = report.GetProperty("ocr_candidate_pages").EnumerateArray().Select(x => x.GetInt32()).ToArray();
        var previews = selectedPages.Select(number => new PagePreview(
            number,
            $"/api/pdf-converter/jobs/{job.Id}/assets/pages/page-{number:0000}.png")).ToArray();
        foreach (var page in selectedPages)
            html = html.Replace(
                $"assets/pages/page-{page:0000}.png",
                $"/api/pdf-converter/jobs/{job.Id}/assets/pages/page-{page:0000}.png",
                StringComparison.Ordinal);
        var warnings = ocrPages.Length == 0
            ? Array.Empty<string>()
            : new[] { $"Review page(s) {string.Join(", ", ocrPages)}; little extractable text was found." };
        return new ConversionResponse(job.Id, html, css, previews, ocrPages, warnings);
    }
}
