using System.Collections.Concurrent;

namespace YourSite.Features.PdfToHtml;

public sealed record ConversionJob(string Id, string Directory, DateTimeOffset Created);

public sealed class ConversionJobStore
{
    private readonly ConcurrentDictionary<string, ConversionJob> _jobs = new();

    public ConversionJob Add(string directory)
    {
        var id = Guid.NewGuid().ToString("N");
        var job = new ConversionJob(id, directory, DateTimeOffset.UtcNow);
        _jobs[id] = job;
        return job;
    }

    public bool TryGet(string id, out ConversionJob job) => _jobs.TryGetValue(id, out job!);
}
