# Projektübersicht – MagicCoinSnapper

## Kurzbeschreibung

**MagicCoinSnapper** ist eine als Progressive Web App (PWA) ausgelegte Blazor WebAssembly-Anwendung zur mobilen Münzerkennung. Sie läuft vollständig clientseitig (kein Backend, keine API) und ist für die Nutzung auf Smartphones ausgelegt.

**Zielgruppe:** Zauberer / Conjurer in Bühnenshows.

Die App befindet sich aktuell im **Gerüststand**: Die MudBlazor-basierte Navigations-Shell steht, die Seiten sind Platzhalter. Die ursprüngliche, JS/OpenCV-basierte Münzerkennung wurde entfernt; ein Nachfolger existiert noch nicht.

## Tech-Stack

| Bereich            | Technologie                                         |
|--------------------|-----------------------------------------------------|
| Framework          | Blazor WebAssembly                                  |
| SDK / Laufzeit     | .NET 10 (`net10.0`, LTS, Support bis 14.11.2028)    |
| SDK-Version lokal  | 10.0.301                                            |
| Projektstruktur    | Single-Project (`Microsoft.NET.Sdk.BlazorWebAssembly`) |
| UI-Komponenten     | MudBlazor 9.5.0 (Layout, Nav, Theme-Provider)       |
| Framework-Pakete   | `Microsoft.AspNetCore.Components.WebAssembly` 10.0.9 (+ `.DevServer`) |
| Sprachfeatures     | Nullable enabled, ImplicitUsings enabled            |
| PWA                | `manifest.webmanifest` + `service-worker.js` / `service-worker.published.js` |
| Styling            | MudBlazor (`_content/MudBlazor/...`), kein Bootstrap, Roboto per System-Fallback (offline-tauglich) |
| UI-Sprache         | Deutsch                                             |
| Hosting (Dev-Test) | IIS Express über `Tools/Start-Lokaler-Test.ps1` (HTTPS Port 44332) |
| Workload           | `wasm-tools` installiert (Release-Optimierung AOT/Trimming) |
| Test-Setup         | keines vorhanden                                    |
| CI / Lint          | keines vorhanden                                    |

## Architektur

```
Program.cs          → WebAssemblyHost bootstrap, RootComponents: #app, HeadOutlet, AddMudServices()
App.razor           → <Router> (NotFoundPage=typeof(NotFound)) + MainLayout
                       (.NET 10: <NotFound>-Renderfragment entfernt → NotFoundPage-Parameter)
_Imports.razor      → globale usings (inkl. MudBlazor, MagicCoinSnapper.Layout / .Pages)

Layout/
  MainLayout.razor     → MudLayout: MudThemeProvider/Popover/Dialog/SnackbarProvider
                        + MudAppBar (Hamburger Icons.Material.Filled.Menu) + Titel
                        + MudDrawer (Variant=Responsive, Breakpoint=Sm, @bind-Open)
                          MudDrawerHeader + MudNavMenu (Startseite/Scan/Einstellungen/Über)
                        + MudMainContent (@Body)
  MainLayout.razor.css → leer (MudBlazor übernimmt Layout)

Components/          → Ordner entfernt (BottomNav gelöscht)

Pages/
  Index.razor        → /           Startseite (nur Überschrift "Startseite", kein Body)
  Camera.razor       → /camera     Kamera-Seite: Live-Kamera (Rückseite), Aufnehmen (PNG),
                                    Bild laden (Upload), Speichern (Download), Löschen,
                                    Scannen (Platzhalter). Collocated JS-Modul Camera.razor.js.
  Camera.razor.js    → ES-Modul: init/capture/stop/downloadFromStream (getUserMedia + canvas + Blob-Download)
  Camera.razor.css   → Scoped Styles (Video/Preview)
  Settings.razor     → /settings   Einstellungen (Platzhalter)
  Ueber.razor        → /ueber      Über-Seite (Lorem-Ipsum-Beispielinhalt)
  NotFound.razor     → /not-found  404-Seite (via Router NotFoundPage, .NET 10)

Services/
  ImageStateService.cs → Scoped DI-Service: hält aktuelles Bild (byte[]+ContentType+Source),
                        ein Bild zur Zeit, Neu überschreibt. Event OnChanged für künftige Scan-Seite.

wwwroot/
  index.html         → MudBlazor CSS (_content/MudBlazor/MudBlazor.min.css)
                       + blazor.webassembly.js + MudBlazor.min.js (danach)
                       + SW-Registrierung mit { updateViaCache: 'none' } (.NET 10)
  web.config         → MIME-Typen (.dll/.wasm/.woff2) + SPA-Fallback für IIS Express
  manifest.webmanifest
  service-worker.js              (Dev)
  service-worker.published.js    (Release; nutzt generierte service-worker-assets.js)
  css/app.css                   (Bootstrap entfernt)
  icon-192.png, icon-512.png, favicon.png

Tools/
  Start-Lokaler-Test.ps1 / .bat     → dotnet publish + IIS Express (HTTPS 44332, HTTP 36643) + optional ngrok
  Build-GitHubPagesRelease.ps1/.bat → Release-Build für GitHub Pages (base-href /MagicCoinSnapper/)
  GenerateBuildInfo.ps1             → generiert BuildInfo.cs (Namespace MagicCoinSnapper, Berlin-TZ)
```

Registrierte Services: Standard-`HttpClient` gegen App-Basisadresse, `MudServices` (MudBlazor), `ImageStateService` (Bildzustand für Weiterverarbeitung).

## Aktueller Projektstatus

**Build-Status:** Kompiliert fehlerfrei (net10.0).
```
dotnet build -c Debug   → 0 Fehler, 0 Warnungen
dotnet publish -c Debug → 0 Fehler (Output: bin\IisExpress\wwwroot)
dotnet publish -c Release → 0 Fehler (Output: bin\Release\net10.0\publish\wwwroot)
```

**Verifiziert (Stand letzte Session):**
- `https://localhost:44332/` über IIS Express → HTTP 200, index.html
- SPA-Fallback: `/ueber`, `/camera` → 200 (web.config Rewrite greift)
- `.wasm`-Assets → 200, `Content-Type: application/wasm`
- `GenerateBuildInfo.ps1` → erzeugt korrekte `BuildInfo.cs` (Namespace `MagicCoinSnapper`)
- Tools-PowerShell-Skripte: Syntax valide

**Git-Status (Branch `main`):** 2 Commits (`8194bb9 Initial commit`, `36d7414 zwischenstand`).
Die gesamte MudBlazor-/.NET-10-/IIS-Express-Umstellung ist **uncommittet**.

Uncommittete Änderungen umfassen:
- .NET 8 → .NET 10 (csproj, Pakete 10.0.9)
- MudBlazor 9.5.0-Integration (Program.cs, _Imports.razor, index.html, MainLayout)
- `App.razor`: `<NotFound>` → `NotFoundPage` (.NET 10-Break)
- `Pages/NotFound.razor` neu, `Pages/Ueber.razor` neu
- `wwwroot/web.config` neu (IIS-Express-tauglich)
- `Components/` gelöscht, `Layout/NavMenu.razor` gelöscht
- `Tools/` neu (5 Skripte), `wwwroot/css/bootstrap/` gelöscht
- `PROJEKTUEBERSICHT.md` aktualisiert

## Offene Punkte / TODOs

- [ ] **`.gitignore` neu anlegen** (gelöscht) – mindestens `bin/`, `obj/`, `.vs/` ausschließen
- [ ] Änderungen committen (MudBlazor + .NET 10 + IIS-Express-Umstellung)
- [ ] Kamera-Workflow in `Pages/Camera.razor` implementieren (`getUserMedia`, benötigt HTTPS oder `localhost`) — **Kamera + Aufnehmen + Laden + Speichern + Anzeige umgesetzt; Scan-Logik noch offen**
- [ ] Münzerkennungs-Pipeline neu aufbauen (Vorgänger-Code wurde entfernt) — "Scannen"-Button ist Platzhalter
- [ ] Scan-/Verarbeitungs-Seite konsumiert `ImageStateService.ImageBytes`
- [ ] `Pages/Settings.razor` mit echten Einstellungen füllen
- [ ] `Pages/Ueber.razor` mit echtem Inhalt füllen (aktuell Lorem Ipsum)
- [ ] PWA-Cache-Strategie beim Release prüfen (stale SW im Dev-Modus beachten)
- [ ] MudBlazor-Theme anpassen (dunkle/theatralische Palette für Bühnenmagie) – optional, später

## Setup & Lauf

Voraussetzung: .NET 10 SDK (10.0.301+) installiert.

```pwsh
# Restore + Build (verifiziert: 0 Fehler / 0 Warnungen)
dotnet build

# Dev-Server starten (Hot Reload, http-Profil)
dotnet run --project MagicCoinSnapper.csproj

# Lokaler Test über IIS Express (HTTPS 44332, mit publish + ngrok optional)
./Tools/Start-Lokaler-Test.bat

# Release-PWA erzeugen
dotnet publish -c Release
# Output: bin\Release\net10.0\publish\wwwroot

# Release für GitHub Pages vorbereiten (base-href /MagicCoinSnapper/)
./Tools/Build-GitHubPagesRelease.bat

# BuildInfo.cs generieren
./Tools/GenerateBuildInfo.ps1 -OutputFile obj/BuildInfo.cs -Version 1.0.0
```

Statisches Hosting: Der `publish/wwwroot`-Ordner kann von jedem statischen Webserver ausgeliefert werden. `index.html` lädt `_framework/blazor.webassembly.js`.

## Hinweise für die Arbeit am Projekt

- **Kamerazugriff** erfordert einen sicheren Kontext (HTTPS oder `localhost`). IIS Express (Port 44332) liefert HTTPS via Selbstsignat-Zertifikat – Browser-Warnung einmalig akzeptieren. Für echte Smartphone-Tests ngrok nutzen (gültiges TLS).
- **IIS Express-Ports:** HTTPS **muss** im Bereich 44300–44399 liegen (IIS-Express-Selbstsignat-Zertifikat nur dort gebunden). Aktuell 44332 (aus `launchSettings.json`). HTTP-Port 36643.
- **`Start-Lokaler-Test.ps1`** macht `dotnet publish` (Debug) → kein Hot Reload. Nach Code-Änderungen Skript neu starten.
- **Service Worker** kann während der Entwicklung veraltete Assets cachen. Bei nicht sichtbaren Änderungen: SW deregistrieren oder Hard-Refresh.
- **`service-worker-assets.js`** wird beim Publish generiert – nicht manuell editieren.
- **`MagicCoinSnapper.csproj.user`** ist maschinenlokal (Visual Studio) – keine nutzerspezifischen Änderungen committen.
- **`.vs/`** enthält IIS-Express-`applicationhost.config` (maschinenlokal) – nicht committen.
- **MudBlazor-Assets** (`_content/MudBlazor/...`) werden vom Service Worker automatisch gecacht (PWA offline-tauglich).
- **Roboto:** bewusst kein Google-Fonts-CDN (offline-tauglich); MudBlazor nutzt System-Sans-Serif (auf Android nativ Roboto).
- Detaillierte Agenten-Hinweise siehe `AGENTS.md`.

## Verifikation

Aktuell existieren keine automatisierten Tests, kein Lint und keine CI. Verifikation erfolgt manuell:

1. `dotnet build` fehlerfrei (0 Fehler, 0 Warnungen)
2. `./Tools/Start-Lokaler-Test.bat` → `https://localhost:44332/` lädt im Browser, Navigation (Startseite / Scan / Einstellungen / Über) funktioniert, Drawer toggelt
3. PWA-Installierbarkeit in DevTools (Application → Manifest + Service Worker prüfen)
4. Optional: `./Tools/GenerateBuildInfo.ps1 -OutputFile obj/BuildInfo.cs -Version 1.0.0` → BuildInfo.cs prüfen

## Nächste Session – Empfohlene erste Schritte

1. `.gitignore` anlegen (`bin/`, `obj/`, `.vs/`, `*.user`)
2. MudBlazor-/.NET-10-Umstellung committen
3. Kamera-Workflow in `Pages/Camera.razor` angehen (Hauptziel der App)
