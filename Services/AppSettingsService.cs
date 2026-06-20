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

    public event Action? OnChanged;

    public async ValueTask LoadAsync(CancellationToken cancellationToken = default)
    {
        var module = await GetModuleAsync(cancellationToken);
        ExpertModeEnabled = await module.InvokeAsync<bool>("getExpertMode", cancellationToken);
        OnChanged?.Invoke();
    }

    public async ValueTask SetExpertModeAsync(bool enabled, CancellationToken cancellationToken = default)
    {
        var module = await GetModuleAsync(cancellationToken);
        ExpertModeEnabled = enabled;
        await module.InvokeVoidAsync("setExpertMode", cancellationToken, enabled);
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
