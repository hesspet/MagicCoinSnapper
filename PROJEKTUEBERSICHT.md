# Projektübersicht – MagicCoinSnapper

## Kurzprofil

**MagicCoinSnapper** ist eine clientseitige Blazor WebAssembly PWA für Zauberer/Conjurer in Bühnenshows. Kein Backend, keine externe API. UI-Sprache Deutsch, Smartphone-first, dunkle Bühnenoptik.

## Aktueller Stand

- **Kamera-Workflow** vollständig: Rückkamera (`getUserMedia`), Foto aufnehmen (PNG), Upload (PNG/JPEG, max 10 MB), Vorschau, Speichern (Download), Löschen.
- **Bildbereitstellung** über `ImageStateService`: hält genau ein aktuelles Bild im Speicher, `OnChanged`-Event für spätere Scan-Pipeline.
- **Münzerkennung / Scan-Logik** ist noch Platzhalter (`Bild scannen` zeigt Snackbar-Hinweis).
- **Settings** strukturell vorbereitet, funktional noch Platzhalter.
- Build: `dotnet build` kompiliert fehlerfrei, 0 Fehler, 0 Warnungen.

## Tech-Stack

| Bereich           | Technologie                                      |
|-------------------|--------------------------------------------------|
| Framework         | Blazor WebAssembly (`Microsoft.NET.Sdk.BlazorWebAssembly`) |
| SDK / Laufzeit    | .NET 10 (`net10.0`, LTS)                         |
| UI-Bibliothek     | MudBlazor 9.5.0                                  |
| Pakete            | `Microsoft.AspNetCore.Components.WebAssembly` 10.0.9 + `.DevServer` |
| Sprachfeatures    | Nullable enabled, ImplicitUsings enabled         |
| PWA               | Manifest + Service Worker (Dev/Published)        |
| Styling           | MudBlazor, keine Bootstrap/CDN-Fonts, System-Font-Stack |
| Hosting (Dev)     | IIS Express HTTPS Port 44332 / HTTP 36643, `dotnet run` auf Ports 7106/5159 |

## Architektur (Kernpunkte)

```
Program.cs     → MudBlazor-Services, HttpClient, ImageStateService
App.razor      → Router mit MainLayout, NotFoundPage
Layout/
  MainLayout.razor     → MudLayout: AppBar, responsive Drawer, NavMenu, Bottom-Action "Scan starten"
  MainLayout.razor.css → Shell-Styles (Safe Areas, Bottom-Action, Hintergrund)
Pages/
  Index.razor   → /           Hero, Statuskarten, Scan-Button
  Camera.razor  → /camera     Kamera/Upload/Vorschau/Speichern + collocated JS-Modul
  Camera.razor.js             getUserMedia (Rückseite), Capture, Blob-Download
  Settings.razor → /settings  Platzhalter mit Infohinweis
  Ueber.razor   → /ueber      Zweck- und Technikbeschreibung
  NotFound.razor → /not-found 404
Services/
  ImageStateService.cs → byte[]+ContentType+Source, OnChanged-Event
```

## Design- und UI-Kontext

- Verbindliches Designsystem: **`DESIGN.md`**. MudBlazor-Theme in `MainLayout.razor` definiert (dunkle Palette, Gold-Primäraction).
- Smartphone-first: `max-width: 520px`, Daumenbedienung, Bottom-Action, Safe Areas.
- Alle Farben/Abstände/Radien/Typografie als CSS-Custom-Properties in `wwwroot/css/app.css`.

## Setup & Befehle

Voraussetzung: .NET 10 SDK installiert.

```pwsh
dotnet build                              # Build verifizieren
dotnet run --project MagicCoinSnapper.csproj  # Dev-Server (Hot Reload)
dotnet publish -c Release                 # PWA-Ausgabe (statisch hostbar)
```

```pwsh
.\Tools\Start-Lokaler-Test.bat            # IIS Express (HTTPS 44332) + optional ngrok
.\Tools\Build-GitHubPagesRelease.bat      # Release für GitHub Pages (base-href /MagicCoinSnapper/)
.\Tools\GenerateBuildInfo.ps1 -OutputFile obj\BuildInfo.cs -Version 1.0.0
```

## Hinweise für die Arbeit

- **Kamerazugriff** braucht sicheren Kontext (HTTPS oder `localhost`). IIS Express liefert HTTPS über Port 44332 (selbstsigniert).
- **Service Worker** kann veraltete Assets cachen → bei Problemen Hard-Refresh oder SW deregistrieren.
- **`service-worker-assets.js`** wird beim Publish generiert, nicht manuell editieren.
- **Nicht committen:** `.vs/`, `bin/`, `obj/`, `MagicCoinSnapper.csproj.user`.
- **UI-Änderungen** müssen `DESIGN.md` folgen.

## Referenzen

- `DESIGN.md` – verbindliches Designsystem (Farben, Typografie, Layouts, Komponentenregeln)
- `PLAN.md` – Umsetzungshistorie, Detailentscheidungen, aufgetretene Probleme
- `AGENTS.md` – Regeln für KI-gestützte Arbeit am Projekt
