# Plan – MudBlazor-Erweiterung + ./Tools + .NET 10 (LTS)

**Stand:** 19.06.2026 – vollständig umgesetzt und verifiziert.

## Ausgangslage / Briefing

- **Hauptanwender:** Zauberer / Conjurer in Bühnenshows
- **Hauptziel:** Smartphoneanwendung
- **Framework:** MudBlazor
- **Anforderungen:** Drawer + Navigation, leere Hauptseite, Seite "Über" mit Lorem Ipsum, Responsive Design, Verzeichnis `./Tools` (Vorlage: `C:\dev\Nasreddins-Camera-Arcanum\Tools`)

## Klärungen (vom Nutzer bestätigt)

1. **Layout-Strategie:** BottomNav entfernen, MudLayout (MudAppBar + MudDrawer Responsive + MudNavMenu) für alle Breakpoints.
2. **Leere Hauptseite:** Nur Seitenüberschrift, kein Body.
3. **Tools-Auswahl:** Build-GitHubPagesRelease (ohne CodeWhale-Variante), Start-Lokaler-Test, GenerateBuildInfo. Kein ConvertFontsToWoff2.py.
4. **MudBlazor-Theme:** Default (Anpassung später).
5. **Route "Über":** `/ueber` (ohne Umlaut in der URL).
6. **Roboto:** System-Fallback (kein CDN, keine lokalen Font-Dateien) – offline-tauglich.
7. **.NET-Version:** .NET 10 (LTS, Support bis 14.11.2028) statt .NET 9 (STS) oder .NET 8.

## Verifizierte Fakten (offizielle Doku)

### MudBlazor 9.5.0 (net8.0/net9.0/net10.0)
- **Package:** `MudBlazor` 9.5.0
- **Program.cs:** `using MudBlazor.Services;` + `builder.Services.AddMudServices();`
- **_Imports.razor:** `@using MudBlazor`
- **index.html CSS:** `_content/MudBlazor/MudBlazor.min.css`
- **index.html JS:** `_content/MudBlazor/MudBlazor.min.js` nach `_framework/blazor.webassembly.js`
- **Responsive Drawer:** `Variant="DrawerVariant.Responsive"` + `Breakpoint` + `@bind-Open`
- **4 Provider** oben im MainLayout: ThemeProvider, PopoverProvider, DialogProvider, SnackbarProvider
- **Bootstrap:** offiziell entfernen

### .NET 10 (LTS)
- Release: 11.11.2025, End of Support: 14.11.2028
- Latest Patch: 10.0.9 (09.06.2026), SDK 10.0.301
- **csproj:** `<TargetFramework>net10.0</TargetFramework>`; SDK `Microsoft.NET.Sdk.BlazorWebAssembly` bleibt
- **Pakete:** `Microsoft.AspNetCore.Components.WebAssembly` + `.DevServer` → 10.0.9
- **Program.cs/Hosting:** `WebAssemblyHostBuilder`-Bootstrap unverändert
- **Service Worker:** Mechanismus unverändert; Template nutzt nun `updateViaCache: 'none'`

### .NET 10 Breaking Changes (dieses Projekt betreffend)
1. `<Router>` `<NotFound>`-Renderfragment entfernt → `NotFoundPage="typeof(NotFound)"` + separate `NotFound.razor` mit `@page`
2. `Blazor-Environment`-Header / `ASPNETCORE_ENVIRONMENT` in launchSettings.json für Standalone-WASM wirkungslos → `<WasmApplicationEnvironmentName>` MSBuild-Property (Defaults Development/Production)
3. `NavLinkMatch.All` ignoriert Query-String/Fragment (für `/` irrelevant)
4. `HttpClient`-Response-Streaming default an (hier ungenutzt)
5. `blazor.boot.json` inlined in `dotnet.js` (kein Custom-Integrity-Skript vorhanden)
6. `BlazorCacheBootResources` entfernt (nicht in csproj)
7. Legacy Mono/Emscripten-JS-Globals (net9-Break, hier nicht referenziert)

## Umgesetzte Änderungen

### Welle 0 – .NET 10 + MudBlazor Setup
- `MagicCoinSnapper.csproj`: `net10.0`, Pakete `10.0.9`, `MudBlazor` 9.5.0
- `Program.cs`: `using MudBlazor.Services;` + `builder.Services.AddMudServices();`
- `_Imports.razor`: `@using MudBlazor`, `@using MagicCoinSnapper.Pages` (Components-Using entfernt, da Ordner gelöscht)
- `App.razor`: `<NotFound>` → `NotFoundPage="typeof(NotFound)"`
- `Pages/NotFound.razor`: neu mit `@page "/not-found"` (RouteAttribute für NotFoundPage erforderlich)
- `wwwroot/index.html`: MudBlazor CSS/JS, SW `updateViaCache: 'none'`, Bootstrap-Link entfernt
- `wwwroot/css/bootstrap/` gelöscht

### Welle A – web.config (für IIS Express)
- `wwwroot/web.config` neu: MIME-Typen (.dll/.wasm/.woff2) + SPA-Fallback (Sub-Routen → index.html)

### Welle B – Layout
- `Layout/MainLayout.razor`: MudLayout (4 Provider + MudAppBar mit Hamburger + MudDrawer Responsive + MudNavMenu + MudMainContent)
- `Layout/MainLayout.razor.css`: geleert (MudBlazor übernimmt)
- `Components/BottomNav.razor`(+.css), `Layout/NavMenu.razor`(+.css) gelöscht
- `Components/`-Ordner entfernt

### Welle C – Seiten
- `Pages/Index.razor`: nur Überschrift "Startseite" (kein Body)
- `Pages/Camera.razor`: MudText-Placeholder
- `Pages/Settings.razor`: MudText-Placeholder
- `Pages/Ueber.razor` neu: `/ueber`, Lorem-Ipsum-Absätze
- `Pages/NotFound.razor` neu: 404-Seite

### Welle D – ./Tools (5 Skripte, Namespace `MagicCoinSnapper`)
- `Start-Lokaler-Test.ps1` / `.bat`: **IIS Express** (dotnet publish → applicationhost.config mit Site+HTTPS-Bindung → iisexpress.exe). HTTPS 44332, HTTP 36643. Optional ngrok.
- `Build-GitHubPagesRelease.ps1` / `.bat`: Repo-Default `MagicCoinSnapper`, base-href `/MagicCoinSnapper/`
- `GenerateBuildInfo.ps1`: Namespace `MagicCoinSnapper`, Berlin-TZ → BuildInfo.cs

### PROJEKTUEBERSICHT.md
- Vollständig aktualisiert (.NET 10 LTS, MudBlazor, IIS-Express, neue Struktur/TODOs)

## Verifikation (alle bestanden)

- `dotnet build -c Debug` → 0 Fehler, 0 Warnungen
- `dotnet publish -c Debug` → 0 Fehler (bin\IisExpress\wwwroot)
- `dotnet publish -c Release` → 0 Fehler (bin\Release\net10.0\publish\wwwroot)
- `https://localhost:44332/` via IIS Express → HTTP 200, index.html
- SPA-Fallback `/ueber`, `/camera` → 200
- `.wasm`-Asset → 200, `Content-Type: application/wasm`
- `GenerateBuildInfo.ps1` → BuildInfo.cs korrekt (Namespace MagicCoinSnapper)
- Tools-PowerShell-Syntax valide
- Dev-Server (`dotnet run`) → HTTP 200, MudBlazor-CSS verlinkt

## Aufgetretene Probleme & Fixes (für künftige Sessions)

1. **`_Imports.razor` CS0234 "Components" nicht vorhanden:** Nach Löschen des leeren `Components/`-Ordners wurde das `@using MagicCoinSnapper.Components` zum Build-Fehler → Using entfernt.
2. **`NotFoundPage` ohne RouteAttribute:** `NotFoundPage="typeof(NotFound)"` fordert ein `RouteAttribute` auf dem Typ → `@page "/not-found"` in `NotFound.razor` ergänzt.
3. **IIS-Express-Pfad mit Leerzeichen:** `"& \`"$iisExe\`"..."` verlor beim Inlining die Quotes → einfache Anführungszeichen: `"& '$iisExe' /config:'$workConfig' ..."`.
4. **Kein web.config im Publish-Output:** .NET 10 Standalone-WASM generiert keine web.config automatisch → manuell in `wwwroot/web.config` abgelegt (wird beim Publish übernommen).
5. **Build-Output wwwroot unvollständig:** `dotnet build` legt nur `_framework` + service-worker ab (kein index.html) → Skript nutzt `dotnet publish` für vollständigen wwwroot.

## Offene Punkte (siehe PROJEKTUEBERSICHT.md → TODOs)

- `.gitignore` neu anlegen
- Änderungen committen
- Kamera-Workflow / Münzerkennungs-Pipeline
- Settings/Ueber mit echtem Inhalt füllen
- MudBlazor-Theme anpassen (optional)
- `wasm-tools`-Workload für Release-Optimierung
