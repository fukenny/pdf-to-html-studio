using System.ComponentModel.DataAnnotations;
using EPiServer.Core;
using EPiServer.DataAbstraction;
using EPiServer.DataAnnotations;

namespace YourSite.Features.PdfToHtml;

[ContentType(
    DisplayName = "PDF to HTML converter",
    GUID = "E6419E41-7A41-4BCD-8D88-BB7C43E6455E",
    Description = "Internal tool for converting selected PDF pages to editable HTML and CSS")]
[AvailableContentTypes(Availability = Availability.None)]
public sealed class PdfToHtmlConverterPage : PageData
{
    [CultureSpecific]
    [Display(Name = "Heading", GroupName = SystemTabNames.Content, Order = 10)]
    public virtual string? Heading { get; set; }

    [CultureSpecific]
    [Display(Name = "Instructions", GroupName = SystemTabNames.Content, Order = 20)]
    public virtual XhtmlString? Instructions { get; set; }
}
