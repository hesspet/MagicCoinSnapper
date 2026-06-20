namespace MagicCoinSnapper.Services;

public sealed class ImageStateService
{
    public byte[]? ImageBytes { get; private set; }
    public string? ContentType { get; private set; }
    public string? Source { get; private set; }
    public byte[]? ExtractedImageBytes { get; private set; }
    public string? ExtractedContentType { get; private set; }

    public bool HasImage => ImageBytes is not null && ImageBytes.Length > 0;
    public bool HasExtractedImage => ExtractedImageBytes is not null && ExtractedImageBytes.Length > 0;

    public event Action? OnChanged;

    public void SetImage(byte[] bytes, string contentType, string source)
    {
        ImageBytes = bytes;
        ContentType = contentType;
        Source = source;
        ExtractedImageBytes = null;
        ExtractedContentType = null;
        OnChanged?.Invoke();
    }

    public void SetExtractedImage(byte[] bytes, string contentType)
    {
        ExtractedImageBytes = bytes;
        ExtractedContentType = contentType;
        OnChanged?.Invoke();
    }

    public void Clear()
    {
        ImageBytes = null;
        ContentType = null;
        Source = null;
        ExtractedImageBytes = null;
        ExtractedContentType = null;
        OnChanged?.Invoke();
    }
}
