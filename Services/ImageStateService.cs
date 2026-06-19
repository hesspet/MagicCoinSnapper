namespace MagicCoinSnapper.Services;

public sealed class ImageStateService
{
    public byte[]? ImageBytes { get; private set; }
    public string? ContentType { get; private set; }
    public string? Source { get; private set; }

    public bool HasImage => ImageBytes is not null && ImageBytes.Length > 0;

    public event Action? OnChanged;

    public void SetImage(byte[] bytes, string contentType, string source)
    {
        ImageBytes = bytes;
        ContentType = contentType;
        Source = source;
        OnChanged?.Invoke();
    }

    public void Clear()
    {
        ImageBytes = null;
        ContentType = null;
        Source = null;
        OnChanged?.Invoke();
    }
}
