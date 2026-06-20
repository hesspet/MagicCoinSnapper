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

---

## Erweiterung: Camera.razor — Kamera, Speichern, Laden, Bereitstellung (umgesetzt 19.06.2026)

### Klärungen
- Speichern: Browser-Download (`<a download>` + Blob via `DotNetStreamReference`)
- Kamera: Rückseite (`facingMode:'environment'`)
- Bildbereistellung: Scoped Service `ImageStateService` (hält `byte[]`)
- Format: PNG (Kamera-Capture); Uploads behalten Original-Content-Type
- Lebenszyklus: Ein Bild zur Zeit, Neu überschreibt
- "Scannen": Platzhalter-Button → `MudSnackbar` "Scan-Funktion folgt später"
- Max. Upload-Größe: 10 MB

### Umgesetzt
- `Services/ImageStateService.cs`: `byte[]? ImageBytes`, `ContentType`, `Source`, `event Action? OnChanged`, `SetImage()`, `Clear()`
- `Program.cs`: `AddScoped<ImageStateService>()`
- `_Imports.razor`: `@using MagicCoinSnapper.Services`
- `Pages/Camera.razor`: UI (Kamera starten/stoppen/aufnehmen, Bild laden via `MudFileUpload`, Vorschau `MudImage`, Speichern/Löschen/Scannen), `IAsyncDisposable` (Kamera-Stream wird beim Verlassen freigegeben)
- `Pages/Camera.razor.js`: collocated ES-Modul (`init`/`capture`/`stop`/`downloadFromStream`), `getUserMedia` mit `facingMode:environment`, `canvas.toDataURL('image/png')`, Blob-Download mit `revokeObjectURL`
- `Pages/Camera.razor.css`: Scoped Styles (Video/Preview, `.hidden`)

### Aufgetretene Probleme & Fixes
1. `MudFileUpload` 9.5: kein `ActivatorContent`-Parameter → `CustomContent` mit `Context="uploader"` + `OnClick="@(async () => await uploader.OpenFilePickerAsync())"`
2. `FilesChanged` Method-Group-Konvertierung schlug fehl → explizites Lambda `@((IBrowserFile? f) => OnFileSelected(f))`
3. `InvokeAsync("init")` Typrückschluss → `InvokeVoidAsync`
4. `DotNetStreamReference.DisposeAsync()` existiert nicht → `ms.DisposeAsync()` (JS-Seite ruft `streamRef.dispose()` auf)

### Verifiziert
- `dotnet build -c Debug` → 0 Fehler, 1 Warnung (MUD0002 Analyzer-Hinweis zu Generic-Inference, nicht blockierend)
- `dotnet publish` → 0 Fehler
- IIS Express HTTPS: `/camera` → 200, `Camera.razor.js`-Modul → 200 (fetchbar, Voraussetzung für JS-Interop)
- Kamera-Capture/Upload/Save: erfordern Browser mit Kamera — nur manuell testbar

### Offen (Folgeschritte)
- Scan-/Verarbeitungs-Seite, die `ImageStateService.ImageBytes` konsumiert
- Echte Münzerkennungs-Pipeline

---

## Erweiterung: Trainer-CLI, ML-Pipeline und PySide6-GUI (umgesetzt 20.06.2026)

### Umfang

Der separate Desktop-Trainer unter `trainer/` wurde als Python-3.12-Paket `mcs_trainer` (editable pip-installiert) vollstaendig umgesetzt: CLI-Kern, ML-Trainingspipeline und PySide6-Annotation-GUI.

### CLI-Befehle (8, alle funktionstuechtig)

```
mcs-trainer import-raw --zip <zip> [--dest trainer/data/raw]
mcs-trainer validate --dataset <dir> [--mode auto|raw|annotated]
mcs-trainer split --dataset <dir> [--train 0.8] [--val 0.1] [--test 0.1] [--seed 42]
mcs-trainer train --dataset <dir> --profile general [--device auto|cuda|cpu] [--epochs 30] [--batch-size 8] [--lr 1e-3] [--seed 42] [--out-dir trainer/runs/coinseg]
mcs-trainer evaluate --run <run> --dataset <dir> [--device auto]
mcs-trainer export-onnx --run <run> [--opset 17]
mcs-trainer package-model --onnx <onnx> --run <run> [--out-dir trainer/model-packages]
mcs-trainer gui [--dataset <dir>]
```

### Wesentliche Entscheidungen

- **Pydantic v2** fuer Raw-/Annotated-Schemas (`RAW_SCHEMA_VERSION`, `ANNOTATED_SCHEMA_VERSION`).
- **Preprocessing spiegelt die PWA exakt**: direkter Stretch-Resize auf 512x512, RGB, /255-Normalisierung, kein Letterboxing; Masken {0,255}->{0,1}.
- **Lazy Imports** fuer optionale Dependencies (ML, GUI), sodass `mcs-trainer --help` auch ohne torch/PySide6 laeuft.
- **U-Net** (compact, base=32, sigmoid output), BCEWithLogitsLoss + Adam, best-by-val-dice Checkpoints, auto-inkrementierende Run-Verzeichnisse.
- **ONNX-Export** mit festen Shapes [1,3,512,512]->[1,1,512,512], Input-Name "input", Output-Name "mask", onnxsim-Vereinfachung.
- **Modellpaket** als zip mit onnx, model.json, metrics.json, preprocessing.json, README.md, SHA256SUMS.txt.
- **GUI**: ImageViewer (Zoom/Pan), MaskEditor (Pinsel/Radierer/Ellipse, Undo/Redo), MetadataPanel (notes/tags/excluded), MainWindow mit Toolbar, Tastatur-Navigation, QProcess-basiertem Training/Export und PWA-Modelluebernahme.
- **Modellverwaltung**: Modelle werden unter `wwwroot/models/<model-id>/` installiert; `wwwroot/models/manifest.json` nutzt `schemaVersion = mcs-model-index-v1`; PWA-Settings bieten die Scan-Modell-Auswahl mit Legacy-Fallback auf `wwwroot/models/coin-segmentation.onnx`.

### Aufgetretene Probleme & Fixes

- `safe_join` in `utils/paths.py` lieferte absolute Pfade, wodurch Bilder in das CWD statt in das Dataset-Verzeichnis geschrieben wurden. Fix: korrektes Joinen gegen das Dataset-Verzeichnis.

### Verifiziert

- 28 Tests via `python -m pytest -q` aus `trainer/` gruen (Import, Raw-/Annotated-Validierung, Splits, CLI-Smoke).
- End-to-End-Smoke: validate -> split (8/1/1) -> train (5 Epochen, val dice 0.99) -> evaluate (test dice 0.99) -> export-onnx (Input [1,3,512,512], Output [1,1,512,512], Bereich 0..1) -> package-model.
- ONNX-Modellvertrag gegen PWA validiert; Modelluebernahme in `wwwroot/models/<model-id>/` mit Manifest und Backup-Verhalten dokumentiert.

### Offen

- Das Smoke-Test-Modell ist KEIN Produktionsmodell. Es muss mit echten Muenzbildern trainiert und ueber den Manifest-basierten Modellworkflow ersetzt werden.
