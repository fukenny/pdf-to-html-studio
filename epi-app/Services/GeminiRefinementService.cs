using System.Net.Http.Json;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Options;

namespace YourSite.Features.PdfToHtml;

public interface IGeminiRefinementService
{
    Task<RefineResponse> RefineAsync(RefineRequest request, CancellationToken cancellationToken);
}

public sealed class GeminiRefinementService : IGeminiRefinementService
{
    private readonly HttpClient _http;
    private readonly PdfConverterOptions _options;

    public GeminiRefinementService(HttpClient http, IOptions<PdfConverterOptions> options)
    {
        _http = http;
        _options = options.Value;
    }

    public async Task<RefineResponse> RefineAsync(RefineRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(_options.GeminiApiKey))
            throw new InvalidOperationException("Gemini is not configured. Add Gemini__ApiKey on the server.");
        if (request.Feedback.Length > 4000 || request.Html.Length > 300_000 || request.Css.Length > 150_000)
            throw new InvalidOperationException("The refinement request is too large.");

        using var message = new HttpRequestMessage(
            HttpMethod.Post,
            $"https://generativelanguage.googleapis.com/v1beta/models/{Uri.EscapeDataString(_options.GeminiModel)}:generateContent");
        message.Headers.Add("x-goog-api-key", _options.GeminiApiKey);
        message.Content = JsonContent.Create(new
        {
            contents = new[] { new { parts = new[] { new { text = BuildPrompt(request) } } } },
            generationConfig = new
            {
                responseMimeType = "application/json",
                responseJsonSchema = new
                {
                    type = "object",
                    properties = new
                    {
                        html = new { type = "string" },
                        css = new { type = "string" },
                        summary = new { type = "string" }
                    },
                    required = new[] { "html", "css", "summary" }
                }
            }
        });
        using var response = await _http.SendAsync(message, cancellationToken);
        response.EnsureSuccessStatusCode();
        using var body = JsonDocument.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
        var text = body.RootElement.GetProperty("candidates")[0].GetProperty("content")
            .GetProperty("parts")[0].GetProperty("text").GetString()
            ?? throw new InvalidOperationException("Gemini returned no result.");
        var refined = JsonSerializer.Deserialize<RefineResponse>(text, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        }) ?? throw new InvalidOperationException("Gemini returned an invalid result.");
        Validate(refined);
        return refined;
    }

    private static string BuildPrompt(RefineRequest request) => $$"""
        You are refining accessible HTML and scoped CSS generated from a PDF for an intranet CMS.
        Follow the editor's feedback. Preserve all facts and data. Do not invent values.
        Return one section fragment whose outer element is
        <section id="pdf-html-content" class="pdf-html">, not a full document. Return CSS inside
        <style id="pdf-html-styles"> and keep every rule inside the .pdf-html scope. Use semantic
        HTML. No scripts, forms, iframes, remote resources, or inline event handlers.

        EDITOR FEEDBACK:
        {{request.Feedback}}

        CURRENT HTML:
        {{request.Html}}

        CURRENT CSS:
        {{request.Css}}
        """;

    private static void Validate(RefineResponse response)
    {
        if (Regex.IsMatch(response.Html, @"<(script|iframe|object|embed|form)\b|\son\w+\s*=", RegexOptions.IgnoreCase))
            throw new InvalidOperationException("The generated HTML contained unsafe elements.");
        if (response.Css.Contains("@import", StringComparison.OrdinalIgnoreCase) ||
            response.Css.Contains("javascript:", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("The generated CSS contained an unsafe reference.");
        if (!response.Html.Contains("pdf-html", StringComparison.Ordinal) ||
            !response.Css.Contains(".pdf-html", StringComparison.Ordinal))
            throw new InvalidOperationException("The generated result was not safely scoped for Epi.");
    }
}
