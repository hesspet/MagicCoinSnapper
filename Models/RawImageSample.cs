namespace MagicCoinSnapper.Models;

public sealed record RawImageSample
{
    public required string Id { get; init; }
    public string? Source { get; init; }
    public string? ContentType { get; init; }
    public long? SizeBytes { get; init; }
    public int? Width { get; init; }
    public int? Height { get; init; }
    public DateTimeOffset CreatedAt { get; init; }
    public string? Notes { get; init; }
}

public sealed record RawImageSampleMetadata
{
    public string? Id { get; init; }
    public string? Source { get; init; }
    public string? ContentType { get; init; }
    public long? SizeBytes { get; init; }
    public int? Width { get; init; }
    public int? Height { get; init; }
    public string? Notes { get; init; }
}

public sealed record RawImageCollectionExport
{
    public int Count { get; init; }
    public DateTimeOffset ExportedAt { get; init; }
    public IReadOnlyList<RawImageSample> Samples { get; init; } = Array.Empty<RawImageSample>();
}
