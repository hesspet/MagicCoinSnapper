# DESIGN.md - MagicCoinSnapper

Dieses Dokument ist das verbindliche Designsystem für MagicCoinSnapper. Es ersetzt alle Marketing- oder Fremdmarken-Referenzen. Jede UI-Änderung muss sich daran orientieren.

## Produktbild

- MagicCoinSnapper ist eine Smartphone-first PWA für Bühnenzauberer.
- Der Hauptkontext ist eine dunkle Bühne, wenig Licht, eine Hand, eine Münze und ein schneller Foto- oder Upload-Flow.
- Die App muss mit einer Hand bedienbar sein, auch unter Zeitdruck vor oder während einer Show.
- UI-Sprache ist Deutsch.
- Die Optik ist präzise, geheimnisvoll und bührentauglich: klare Flächen, warme Goldakzente, starke Kontraste, keine Marketing- oder Admin-Ästhetik.

## UI-Technik

- MudBlazor 9.5.0 ist die einzige UI-Bibliothek.
- Keine Bootstrap-Klassen, keine fremden Component Libraries, keine CDN-Fonts.
- Layout, Navigation, Buttons, Inputs, Dialoge, Drawer, Snackbar, Tabs und Cards werden mit MudBlazor umgesetzt.
- Eigene CSS-Klassen sind nur für Layout-Templates, Design-Tokens, Kamera-/Bildflächen und notwendige Feinanpassungen erlaubt.
- Icons kommen aus MudBlazor/Material Icons, sofern kein zwingender Produktgrund fuer eigene SVGs besteht.

## Design Tokens

### Farben

| Token | Dunkel | Hell | Verwendung |
|---|---:|---:|---|
| `--mcs-bg` | `#07070a` | `#f6f1e8` | App-Hintergrund |
| `--mcs-bg-soft` | `#101016` | `#efe5d5` | Seitenflächen, AppBar, Bottom-Bar |
| `--mcs-surface` | `#171720` | `#fff9ef` | Cards, Panels, Drawer |
| `--mcs-surface-raised` | `#20202b` | `#ffffff` | aktive Flächen, Dialoge |
| `--mcs-border` | `#343442` | `#d7cbb8` | Hairlines, Trenner, Input-Border |
| `--mcs-text` | `#f5f1e8` | `#211b12` | Primärer Text |
| `--mcs-text-muted` | `#b8b2a7` | `#635b4e` | Sekundärer Text, Hilfetext |
| `--mcs-text-disabled` | `#77727f` | `#9b907f` | Disabled, Platzhalter |
| `--mcs-gold` | `#d8a83f` | `#9a6d13` | Primäraktion, Scan-Fokus, aktive Navigation |
| `--mcs-gold-strong` | `#f2c35b` | `#6f4c08` | Hover/Highlight, wichtige Statuspunkte |
| `--mcs-gold-soft` | `#3a2b12` | `#f3dfb4` | dezente Goldflächen |
| `--mcs-primary-contrast` | `#120f08` | `#fff9ef` | Text auf Primäraktionen |
| `--mcs-red` | `#ff5a5f` | `#b3261e` | Fehler, kritische Hinweise |
| `--mcs-error-bg` | `#5b1518` | `#f8d7d4` | Fehlerflächen |
| `--mcs-error-contrast` | `#ffffff` | `#3d0b08` | Text auf Fehlerflächen |
| `--mcs-green` | `#49d17d` | `#247a45` | Erfolg, bereit, gespeichert |
| `--mcs-blue` | `#64b5f6` | `#1e6aa8` | Info, technische Hinweise |
| `--mcs-media-bg` | `#000000` | `#000000` | Kamera-/Bildflächen |
| `--mcs-media-bg-soft` | `#050507` | `#050507` | vorbereitete Bildflächen |
| `--mcs-media-text` | `#f5f1e8` | `#f5f1e8` | Text auf dunklen Medienflächen |
| `--mcs-bottom-bar-bg` | `rgba(16, 16, 22, 0.96)` | `rgba(255, 249, 239, 0.96)` | mobile Bottom-Bar |
| `--mcs-camera-overlay` | `rgba(0, 0, 0, 0.58)` | `rgba(0, 0, 0, 0.58)` | Kamera-Abdunklung |
| `--mcs-glow-gold` | `rgba(216, 168, 63, 0.16)` | `rgba(154, 109, 19, 0.12)` | dezente Fokusverläufe |
| `--mcs-glow-gold-strong` | `rgba(216, 168, 63, 0.22)` | `rgba(154, 109, 19, 0.18)` | stärkere Fokusverläufe |
| `--mcs-gold-border` | `rgba(216, 168, 63, 0.34)` | `rgba(154, 109, 19, 0.26)` | Gold-Hairlines |
| `--mcs-gold-border-strong` | `rgba(216, 168, 63, 0.42)` | `rgba(154, 109, 19, 0.38)` | starke Gold-Hairlines |

Regeln:

- Primärfarbe ist Gold, nicht Blau.
- Default ist Dunkel. Helle Vollseiten sind erlaubt, wenn sie denselben Werkzeugcharakter behalten und nicht nach Marketing- oder Admin-Oberfläche wirken.
- Kamera- und Medienflächen dürfen auch im hellen Design dunkel bleiben.
- Statusfarben werden sparsam eingesetzt und dürfen Gold nicht ersetzen.
- Textkontrast muss auf echten Smartphone-Displays bei geringer Helligkeit lesbar bleiben.

### Spacing

Basis ist ein 4px-Raster.

| Token | Wert | Verwendung |
|---|---:|---|
| `--mcs-space-1` | `4px` | feine Abstände |
| `--mcs-space-2` | `8px` | Icon/Text, kompakte Gruppen |
| `--mcs-space-3` | `12px` | kleine Innenabstände |
| `--mcs-space-4` | `16px` | Standard-Padding mobil |
| `--mcs-space-5` | `20px` | Formulargruppen |
| `--mcs-space-6` | `24px` | Cards, Seitenabschnitte |
| `--mcs-space-8` | `32px` | größere Blöcke |
| `--mcs-space-10` | `40px` | Desktop-Abschnitte |

Regeln:

- Mobile Seiten haben horizontal `16px` Padding.
- Primäraktionen liegen in Daumennähe am unteren Rand.
- Vertikale Abstände sind kompakt; die App ist ein Werkzeug, keine Landingpage.

### Radius

| Token | Wert | Verwendung |
|---|---:|---|
| `--mcs-radius-xs` | `6px` | Badges, kleine Markierungen |
| `--mcs-radius-sm` | `10px` | Inputs, kleine Buttons |
| `--mcs-radius-md` | `14px` | Cards, Panels, Menus |
| `--mcs-radius-lg` | `20px` | Kamera-Preview, große Cards |
| `--mcs-radius-pill` | `999px` | Chips, Bottom-Actions |

Regeln:

- Keine eckigen Standard-Container.
- Keine uebertrieben weichen Marketing-Karten.
- Kamera- und Bildflächen bekommen den größten Radius.

### Typografie

System-Font-Stack: `Inter, Segoe UI, Roboto, Arial, sans-serif`. Keine extern geladenen Fonts.

| Token | Größe | Gewicht | Zeilenhöhe | Verwendung |
|---|---:|---:|---:|---|
| `--mcs-type-display` | `28px` | `700` | `1.15` | Start-/Flow-Titel mobil |
| `--mcs-type-title` | `22px` | `700` | `1.2` | Seitentitel |
| `--mcs-type-subtitle` | `18px` | `600` | `1.3` | Card-Titel, Gruppen |
| `--mcs-type-body` | `16px` | `400` | `1.5` | Standardtext |
| `--mcs-type-body-strong` | `16px` | `600` | `1.45` | wichtige Werte, Labels |
| `--mcs-type-small` | `14px` | `400` | `1.45` | Hilfetext, Meta |
| `--mcs-type-caption` | `12px` | `600` | `1.3` | Badges, Status |
| `--mcs-type-button` | `16px` | `700` | `1` | Hauptbuttons |

Regeln:

- Titel sind kurz und handlungsorientiert.
- Keine dekorativen Display-Fonts.
- Zahlen, Status und Scan-Ergebnisse müssen sofort erfassbar sein.

### Touch, Höhen und Bewegung

- Mindest-Touchziel: `48px` Höhe und Breite.
- Primärbutton mobil: `56px` Höhe.
- Bottom-Action-Bar: `72px` Mindesthöhe plus Safe-Area.
- AppBar mobil: `56px`, Desktop: `64px`.
- Animationen: `120ms` bis `180ms`, easing `ease-out`.
- Keine langen Parallax-, Marketing- oder Scroll-Animationen.

## MudBlazor-Einschraenkungen

- `MudTheme` bildet die Tokens ab; keine verstreuten Hex-Werte in Komponenten.
- `MudButton` nutzt `Variant.Filled` für Primäraktionen und `Variant.Outlined` oder `Variant.Text` für Nebenaktionen.
- `Color.Primary` ist Gold. `Color.Secondary` bleibt dunkel/dezent.
- `MudCard` ist fuer strukturierte Inhalte erlaubt, aber nicht fuer jede kleine Textgruppe.
- `MudPaper` darf fuer App-Shell-, Kamera- und Einstellungs-Panels genutzt werden.
- `MudDialog` nur für echte Unterbrechungen: Berechtigungen, Löschen, kritische Fehler.
- `MudSnackbar` nur für kurze Rückmeldungen: gespeichert, Fehler, offline, Upload bereit.
- `MudDrawer` auf Desktop erlaubt; mobil keine dauerhafte Seitenleiste.
- `MudGrid` ist für einfache Raster erlaubt; für Smartphone-Flows bevorzugt einspaltige Flex-/Stack-Layouts.
- `MudTable` ist mobil zu vermeiden; Ergebnisse als Cards oder Listen darstellen.
- Keine Inline-Styles außer dynamischen, komponentennahen Werten wie Bildgrößen aus Laufzeitdaten.

## Layoutvorlagen

### `app-shell`

Zweck: globale PWA-Hülle.

- Hintergrund `--mcs-bg` über die gesamte Viewport-Höhe.
- `MudAppBar` flach, mit Logo/Titel links und optionaler Statusaktion rechts.
- Desktop darf `MudDrawer` fuer Navigation nutzen.
- Mobile Navigation wird als Bottom-Navigation oder Bottom-Actions umgesetzt, nicht als permanenter Drawer.
- Content beruecksichtigt `safe-area-inset-top` und `safe-area-inset-bottom`.

### `mobile-bottom-action`

Zweck: feste Hauptaktion fuer Daumenbedienung.

- Am unteren Rand fixiert oder sticky.
- Hintergrund `--mcs-bg-soft` mit oberer Hairline `--mcs-border`.
- Primäraktion als goldener `MudButton` mit `56px` Höhe und Pill-Radius.
- Nebenaktionen links/rechts nur, wenn sie im Flow wirklich gebraucht werden.
- Muss `env(safe-area-inset-bottom)` einrechnen.

### `mobile-page`

Zweck: Standardseite fuer Smartphone.

- Einspaltig, max. Breite `520px`, zentriert auf größeren Screens.
- Padding mobil `16px`, Desktop `24px` bis `32px`.
- Seitenkopf: kurzer Titel, optional ein Satz Kontext.
- Inhalt in klaren Abschnitten mit `24px` Abstand.
- Hauptaktion unten, nicht versteckt in der Kopfzeile.

### `camera-flow`

Zweck: Foto aufnehmen, Bild laden, Scan vorbereiten.

- Kamera-/Bildbereich ist die visuelle Mitte der Seite.
- Preview als dunkles Panel mit Radius `20px`, Hairline und optionaler Gold-Fokusmarke.
- Overlay-Hinweise kurz: z. B. `Hand ruhig halten`, `Münze sichtbar platzieren`.
- Primäraktion: `Foto aufnehmen` oder `Bild verwenden`.
- Sekundäraktionen: `Aus Galerie laden`, `Erneut aufnehmen`, `Abbrechen`.
- Berechtigungsfehler zeigen konkrete nächste Schritte, keinen generischen Fehlertext.

### `settings`

Zweck: Einstellungen ohne Ablenkung.

- Gruppen als `MudPaper`/`MudCard` auf `--mcs-surface`.
- Jede Gruppe hat Titel, optional Hilfetext, dann Controls.
- Toggles und Selects müssen große Touchziele behalten.
- Gefährliche Aktionen stehen am Ende und nutzen Rot nur für die konkrete Aktion.

### `placeholder`

Zweck: leere, kommende oder nicht verfügbare Zustände.

- Card mit dezentem Icon, kurzem Titel und einem hilfreichen Satz.
- Wenn möglich eine konkrete Aktion anbieten.
- Keine generischen Illustrationen, keine Maskottchen, keine Marketinggrafiken.
- Offline-/Berechtigungs-/Kein-Bild-Zustände müssen eindeutig unterscheidbar sein.

## Komponentenregeln

- Primärbuttons sind gold, breit und unten erreichbar.
- Sekundärbuttons sind outlined oder textbasiert.
- Inputs sind klar beschriftet und nicht nur über Placeholder erklärt.
- Cards trennen Funktionen, nicht Dekoration.
- Badges zeigen Status wie `Bereit`, `Offline`, `Demo`, `Fehler`.
- Icons unterstuetzen Text, ersetzen ihn aber nicht bei wichtigen Aktionen.
- Loading States zeigen, was passiert: `Bild wird vorbereitet`, `Scan läuft`, `Wird gespeichert`.

## Do

- I18N: Bei Texten Deutsche Rechtschreibung, nutze Umlaute und ß bei Texten.
- Smartphone zuerst entwerfen und dann fuer Desktop erweitern.
- Dunkles Design als Default konsequent halten; helles Design bleibt ruhig, warm und werkzeughaft.
- Gold nur für Fokus, Fortschritt und primäre Aktionen verwenden.
- Kamera- und Bildflächen groß, ruhig und kontrastreich darstellen.
- Deutsche, kurze, aktive Beschriftungen verwenden.
- Offline- und Berechtigungszustände als normale PWA-Zustände behandeln.
- MudBlazor-Komponenten bevorzugen und nur gezielt stylen.

## Don't

- Keine Clay.com-, SaaS-Marketing-, Cream-Canvas- oder 3D-Maskottchen-Ästhetik.
- Keine Bootstrap-Klassen oder zweite UI-Bibliothek.
- Keine hellgrauen Admin-Oberflächen und keine beliebige SaaS-Marketing-Ästhetik.
- Keine Navigation, die auf Mobile wichtige Aktionen nach oben oder in Menues versteckt.
- Keine langen Texte in Buttons oder Kamera-Overlays.
- Keine Tabellen für mobile Scan-Ergebnisse.
- Keine Hover-only Interaktionen; Touch muss vollständig funktionieren.
- Keine neuen Farben, Abstände oder Radien ohne Token-Erweiterung in diesem Dokument.

## Umsetzungsreihenfolge

1. `MudTheme` mit Farb-, Typografie-, Radius- und Default-Komponentenwerten definieren.
2. `app-shell` auf dunkle PWA-Hülle, Safe-Areas und mobile Navigation bringen.
3. `mobile-page` und `mobile-bottom-action` als wiederverwendbare Struktur etablieren.
4. `camera-flow` für Aufnahme, Galerie, Preview und Berechtigungen gestalten.
5. `settings` und `placeholder` vereinheitlichen.
6. Bestehende Seiten auf Tokens, MudBlazor-only und deutsche Microcopy prüfen.
7. Visuelle Sonderfälle entfernen: Inline-Hex, Bootstrap-Reste, helle Marketing-Flächen.

## Verifikation

- `DESIGN.md` ist die Quelle für UI-Entscheidungen; Abweichungen müssen bewusst begründet werden.
- Suche nach Bootstrap-Klassen und fremden UI-Bibliotheken muss ohne neue Treffer bleiben.
- Suche nach Inline-Hex-Werten in Komponenten muss begründet oder bereinigt sein.
- Build, Lint und Tests müssen nach UI-Änderungen laufen, sofern im Projekt vorhanden.
- Manuelle Prüfung auf einem Smartphone-Viewport: `360x800`, `390x844`, `430x932`.
- Touchziele mindestens `48px`; Hauptaktion unten erreichbar.
- Dark-Mode-Kontrast bei niedriger Displayhelligkeit prüfen.
- PWA-Zustände prüfen: offline, fehlende Kamera-Berechtigung, kein Bild, Fehler, Erfolg.
