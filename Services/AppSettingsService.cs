using Microsoft.JSInterop;

namespace MagicCoinSnapper.Services;

public sealed class AppSettingsService : IAsyncDisposable
{
    private const string ModulePath = "./js/app-settings.js";

    private readonly Lazy<Task<IJSObjectReference>> moduleTask;

    public AppSettingsService(IJSRuntime jsRuntime)
    {
        moduleTask = new Lazy<Task<IJSObjectReference>>(() =>
            jsRuntime.InvokeAsync<IJSObjectReference>("import", ModulePath).AsTask());
    }

    public bool ExpertModeEnabled { get; private set; }

    public bool ScanDebugModeEnabled { get; private set; }

    public bool IsDarkDesign { get; private set; } = true;

    public string? SelectedModelId { get; private set; }

    public event Action? OnChanged;

    public async ValueTask LoadAsync(CancellationToken cancellationToken = default)
    {
        var module = await GetModuleAsync(cancellationToken);
        ExpertModeEnabled = await module.InvokeAsync<bool>("getExpertMode", cancellationToken);
        ScanDebugModeEnabled = await module.InvokeAsync<bool>("getScanDebugMode", cancellationToken);
        IsDarkDesign = await module.InvokeAsync<bool>("getIsDarkDesign", cancellationToken);
        SelectedModelId = await module.InvokeAsync<string?>("getSelectedModelId", cancellationToken);
        OnChanged?.Invoke();
    }

    public async ValueTask SetExpertModeAsync(bool enabled, CancellationToken cancellationToken = default)
    {
        var module = await GetModuleAsync(cancellationToken);
        ExpertModeEnabled = enabled;
        await module.InvokeVoidAsync("setExpertMode", cancellationToken, enabled);
        OnChanged?.Invoke();
    }

    public async ValueTask SetScanDebugModeAsync(bool enabled, CancellationToken cancellationToken = default)
    {
        var module = await GetModuleAsync(cancellationToken);
        ScanDebugModeEnabled = enabled;
        await module.InvokeVoidAsync("setScanDebugMode", cancellationToken, enabled);
        OnChanged?.Invoke();
    }

    public async ValueTask SetIsDarkDesignAsync(bool isDarkDesign, CancellationToken cancellationToken = default)
    {
        var module = await GetModuleAsync(cancellationToken);
        IsDarkDesign = isDarkDesign;
        await module.InvokeVoidAsync("setIsDarkDesign", cancellationToken, isDarkDesign);
        OnChanged?.Invoke();
    }

    public async ValueTask SetSelectedModelIdAsync(string? modelId, CancellationToken cancellationToken = default)
    {
        var module = await GetModuleAsync(cancellationToken);
        SelectedModelId = string.IsNullOrWhiteSpace(modelId) ? null : modelId;
        await module.InvokeVoidAsync("setSelectedModelId", cancellationToken, SelectedModelId);
        OnChanged?.Invoke();
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
}
