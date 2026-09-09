namespace YourSite.Features.PdfToHtml;

public sealed record PdfConverterViewModel(PdfToHtmlConverterPage CurrentPage);

public sealed record ConversionResponse(
    string JobId,
    string Html,
    string Css,
    IReadOnlyList<PagePreview> Pages,
    IReadOnlyList<int> OcrCandidates,
    IReadOnlyList<string> Warnings);

public sealed record PagePreview(int Number, string ImageUrl);

public sealed record RefineRequest(string JobId, string Html, string Css, string Feedback);

public sealed record RefineResponse(string Html, string Css, string Summary);
