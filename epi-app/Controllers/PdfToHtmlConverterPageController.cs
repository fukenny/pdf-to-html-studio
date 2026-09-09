using EPiServer.Web.Mvc;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace YourSite.Features.PdfToHtml;

[Authorize]
public sealed class PdfToHtmlConverterPageController : PageController<PdfToHtmlConverterPage>
{
    public IActionResult Index(PdfToHtmlConverterPage currentPage) =>
        View("~/Features/PdfToHtml/Views/Index.cshtml", new PdfConverterViewModel(currentPage));
}
