# Design – MagicCoinSnapper

Dieses Dokument hält die verbindlichen Designentscheidungen für das Projekt fest.
Es ist die Referenz für alle UI-/Komponenten-/Style-Entscheidungen und wird in `AGENTS.md` referenziert.

## Subjekt & Zielgruppe

- **Subjekt:** Werkzeug für Bühnenzauberer / Conjurer zur Münzerkennung auf dem Smartphone.
- **Zielgruppe:** Zauberer, die während einer Bühnenshow eine Hand mit Münze fotografieren und das Bild weiterverarbeiten wollen.
- **Single Job der App:** Ein Bild aufnehmen oder laden, bereitstellen, (später) scannen.

## Tech-Stack (designrelevant)

| Bereich      | Entscheidung                                            |
|--------------|---------------------------------------------------------|
| Framework    | Blazor WebAssembly (.NET 10 LTS)                        |
| UI-Bibliothek| MudBlazor 9.5.0 (einzige UI-Lib, kein Bootstrap)        |
| Theme        | Default MudBlazor-Theme (Anpassung später möglich)      |
| Schrift      | System-Sans-Serif (Roboto auf Android nativ); bewusst kein Google-Fonts-CDN (offline-tauglich) |
| Layout       | MudLayout: MudAppBar + MudDrawer Responsive + MudNavMenu |
| UI-Sprache   | Deutsch                                                 |
| PWA          | Standalone, offline-tauglich, Service Worker cacht MudBlazor-Assets automatisch |

## Layout-System

### Shell (`Layout/MainLayout.razor`)

```
MudThemeProvider / MudPopoverProvider / MudDialogProvider / MudSnackbarProvider
MudLayout
├── MudAppBar (Elevation=1)
│   ├── MudIconButton (Icons.Material.Filled.Menu, Edge=Start, OnClick=ToggleDrawer)
│   └── Titel "MagicCoinSnapper"
├── MudDrawer (Variant=Responsive, Breakpoint=Sm, @bind-Open)
│   ├── MudDrawerHeader → MudText Typo.h6 "MagicCoinSnapper"
│   └── MudNavMenu
│       ├── Startseite  → /
│       ├── Scan        → /camera
│       ├── Einstellungen → /settings
│       └── Über        → /ueber
└── MudMainContent → @Body
```

### Responsive Verhalten
- **Desktop (≥ Sm):** Drawer permanent eingeblendet, schiebt Content.
- **Mobile (< Sm):** Drawer als Overlay, Hamburger-Toggle in AppBar, schließt bei Navigation.
- **Default-Zustand:** `_drawerOpen = false` (mobile-first; Desktop-Nutzer öffnen einmal).

## Farbsystem

Aktuell: **Default MudBlazor-Palette** (Primary = Indigo, Background = Weiß).
Keine projektspezifischen Farben definiert.

> Offen für später: dunkle/theatralische Palette für Bühnenmagie (in `PROJEKTUEBERSICHT.md` als TODO geführt).
> Bei Anpassung: `MudTheme` mit `PaletteLight`/`PaletteDark` in `MainLayout.razor` definieren und hier dokumentieren.

## Typografie

| Rolle      | MudBlazor-Typo | Verwendung                          |
|------------|----------------|-------------------------------------|
| Seiten-Titel | `Typo.h4`    | Überschrift jeder Seite             |
| App-Titel  | `Typo.h6`      | Drawer-Header                        |
| Body       | `Typo.body1`   | Fließtext, Platzhalter              |

Keine zusätzlichen Webfonts eingebunden; MudBlazor nutzt System-Sans-Serif (auf Android Roboto).

## Komponenten-Konventionen

- **Buttons:** `MudButton` mit `Variant.Filled` (primäre Aktion) bzw. `Variant.Outlined` (sekundär). `Color.Primary` für die Hauptaktion einer Seite.
- **Text:** `MudText` mit `Typo`-Parameter, `GutterBottom="true"` für Abstand darunter.
- **Bildvorschau:** `MudImage` mit `Fluid="true"`, `ObjectFit="ObjectFit.Contain"`, `max-height: 60vh` (scoped CSS).
- **Datei-Upload:** `MudFileUpload<IBrowserFile>` mit `CustomContent`-Activator (MudBlazor 9.5), `Accept`/`MaxFileSize` immer explizit.
- **Feedback:** `ISnackbar` mit `Severity` (Info/Error), deutsche Meldungen, kein Apologizing.
- **Container:** `MudContainer MaxWidth="MaxWidth.ExtraSmall"` für mobile-first Seiteninhalte.

## Seiten-Spezifika

### `/` (Index)
- Nur `MudText Typo.h4 "Startseite"`, kein Body. Bewusst leere Leinwand für künftigen Inhalt.

### `/camera` (Camera) — Hauptseite
- Mobile-first, `MudContainer MaxWidth=ExtraSmall`, Flex-Column mit `gap: 1rem`.
- **Kamera:** `<video id="cam" playsinline autoplay muted>` (iOS-kompatibel), `.hidden`-Klasse toggelt Sichtbarkeit.
- **Capture:** PNG via `canvas.toDataURL('image/png')`.
- **Upload:** `image/png,image/jpeg`, max 10 MB, Original-Content-Type wird bewahrt (keine Konvertierung).
- **Vorschau:** Daten-URL (`data:{contentType};base64,...`) — kein Object-URL, kein Revocation-Aufwand.
- **Speichern:** Browser-Download via `DotNetStreamReference` + JS-Blob (`<a download>`), `revokeObjectURL` nach Klick.
- **Scannen:** Platzhalter, `Severity.Info`-Snackbar "Scan-Funktion folgt später."
- **Dispose:** `IAsyncDisposable` — Kamera-Stream wird beim Verlassen freigegeben (sonst bleibt LED an).

### `/settings`, `/ueber`
- Platzhalter (`MudText`), `/ueber` mit Lorem-Ipsum-Beispielinhalt.

### `/not-found` (NotFound)
- Über `Router.NotFoundPage` (.NET 10), benötigt `@page "/not-found"` (RouteAttribute-Pflicht).

## State-Management

- **`ImageStateService`** (Scoped): hält aktuelles Bild als `byte[]` + `ContentType` + `Source` ("camera"|"upload").
- Ein Bild zur Zeit; `SetImage()` überschreibt; `OnChanged`-Event für künftige Scan-Seite.
- In Blazor WASM = Tab-Singleton (ein Circuit pro Tab), persists across navigations.
- Keine IndexedDB, keine Query-Strings für Bild-Payloads.

## IIS Express & Secure Context

- `getUserMedia` erfordert HTTPS/`localhost`. IIS Express auf Port **44332** (Bereich 44300–44399, Selbstsignat-Zertifikat) erfüllt das.
- `wwwroot/web.config`: MIME-Typen (`.dll`, `.wasm`, `.woff2`) + SPA-Fallback (Sub-Routen → `index.html`).

## Don'ts

- **Kein Bootstrap** (entfernt, MudBlazor übernimmt alles).
- **Kein Google-Fonts-CDN** (offline-tauglich bleiben).
- **Keine Kommentare im Code** (außer explizit angefordert, siehe `AGENTS.md`).
- **Keine `streamRef.DisposeAsync()`** — `DotNetStreamReference` hat keine; JS-Seite disposet, C# disposet den `MemoryStream`.
- **Kein `ActivatorContent`** bei `MudFileUpload` 9.5 → `CustomContent` + `OpenFilePickerAsync()`.
- **Kein `<NotFound>`-Renderfragment** im Router (.NET 10) → `NotFoundPage`-Parameter.

## Änderungsprotokoll

| Datum       | Änderung                                                      |
|-------------|---------------------------------------------------------------|
| 19.06.2026  | Erstellt: MudBlazor-/.NET-10-Umstellung + Kamera-Feature      |
