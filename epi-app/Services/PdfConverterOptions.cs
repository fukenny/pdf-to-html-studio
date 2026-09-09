namespace YourSite.Features.PdfToHtml;

public sealed class PdfConverterOptions
{
    public string PythonExecutable { get; set; } = "python3";
    public string ConverterProjectPath { get; set; } = "";
    public string WorkPath { get; set; } = "App_Data/pdf-converter";
    public long MaxUploadBytes { get; set; } = 50 * 1024 * 1024;
    public int TimeoutSeconds { get; set; } = 180;
    public string GeminiModel { get; set; } = "gemini-3.7-flash";
    public string? GeminiApiKey { get; set; }
}
