using MagicCoinSnapper.Models;
using Microsoft.JSInterop;

namespace MagicCoinSnapper.Services;

public sealed class RawImageCollectionService : IAsyncDisposable
{
    private const string ModulePath = "./Pages/Collection.razor.js";

    private readonly Lazy<Task<IJSObjectReference>> moduleTask;

    public RawImageCollectionService(IJSRuntime jsRuntime)
    {
        moduleTask = new Lazy<Task<IJSObjectReference>>(() =>
            jsRuntime.InvokeAsync<IJSObjectReference>("import", ModulePath).AsTask());
    }

    public bool IsLoading { get; private set; }
    public int Count { get; private set; }
    public IReadOnlyList<RawImageSample> Samples { get; private set; } = Array.Empty<RawImageSample>();

    public event Action? OnChanged;

    public async ValueTask<IReadOnlyList<RawImageSample>> ListAsync(CancellationToken cancellationToken = default)
    {
        var module = await GetModuleAsync(cancellationToken);
        Samples = await module.InvokeAsync<RawImageSample[]>("listRawImages", cancellationToken)
            ?? Array.Empty<RawImageSample>();
        Count = Samples.Count;
        NotifyChanged();
        return Samples;
    }

    public async ValueTask RefreshAsync(CancellationToken cancellationToken = default)
    {
        IsLoading = true;
        NotifyChanged();

        try
        {
            await ListAsync(cancellationToken);
        }
        finally
        {
            IsLoading = false;
            NotifyChanged();
        }
    }

    public async ValueTask<RawImageSample?> SaveAsync(
        RawImageSampleMetadata metadata,
        string dataUrl,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(metadata);
        ArgumentException.ThrowIfNullOrWhiteSpace(dataUrl);

        var module = await GetModuleAsync(cancellationToken);
        var savedSample = await module.InvokeAsync<RawImageSample?>(
            "saveRawImage",
            cancellationToken,
            metadata,
            dataUrl);

        if (savedSample is not null)
        {
            var samples = Samples.ToList();
            samples.Insert(0, savedSample);
            Samples = samples;
            Count = Samples.Count;
            NotifyChanged();
        }

        return savedSample;
    }

    public async ValueTask DeleteAsync(string id, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);

        var module = await GetModuleAsync(cancellationToken);
        await module.InvokeVoidAsync("deleteRawImage", cancellationToken, id);
        Samples = Samples.Where(sample => sample.Id != id).ToArray();
        Count = Samples.Count;
        NotifyChanged();
    }

    public async ValueTask<RawImageCollectionExport?> ExportAsync(CancellationToken cancellationToken = default)
    {
        var module = await GetModuleAsync(cancellationToken);
        return await module.InvokeAsync<RawImageCollectionExport?>("exportRawImages", cancellationToken);
    }

    public async ValueTask DisposeAsync()
    {
        if (!moduleTask.IsValueCreated)
        {
            return;
        }

        var module = await moduleTask.Value;
        await module.DisposeAsync();
    }

    private Task<IJSObjectReference> GetModuleAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return moduleTask.Value;
    }

    private void NotifyChanged() => OnChanged?.Invoke();
}
