using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace YourSite.Features.PdfToHtml;

public static class PdfToHtmlServiceCollectionExtensions
{
    public static IServiceCollection AddPdfToHtmlConverter(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.Configure<PdfConverterOptions>(configuration.GetSection("PdfConverter"));
        services.AddSingleton<ConversionJobStore>();
        services.AddScoped<IPdfConversionService, PythonPdfConversionService>();
        services.AddHttpClient<IGeminiRefinementService, GeminiRefinementService>();
        return services;
    }
}
