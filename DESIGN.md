# DESIGN.md - MagicCoinSnapper

Dieses Dokument ist das verbindliche Designsystem fuer MagicCoinSnapper. Es ersetzt alle Marketing- oder Fremdmarken-Referenzen. Jede UI-Aenderung muss sich daran orientieren.

## Produktbild

- MagicCoinSnapper ist eine Smartphone-first PWA fuer Buehnenzauberer.
- Der Hauptkontext ist eine dunkle Buehne, wenig Licht, eine Hand, eine Muenze und ein schneller Foto- oder Upload-Flow.
- Die App muss mit einer Hand bedienbar sein, auch unter Zeitdruck vor oder waehrend einer Show.
- UI-Sprache ist Deutsch.
- Die Optik ist praezise, geheimnisvoll und buehnentauglich: klare Flaechen, warme Goldakzente, starke Kontraste, keine Marketing- oder Admin-Aesthetik.

## UI-Technik

- MudBlazor 9.5.0 ist die einzige UI-Bibliothek.
- Keine Bootstrap-Klassen, keine fremden Component Libraries, keine CDN-Fonts.
- Layout, Navigation, Buttons, Inputs, Dialoge, Drawer, Snackbar, Tabs und Cards werden mit MudBlazor umgesetzt.
- Eigene CSS-Klassen sind nur fuer Layout-Templates, Design-Tokens, Kamera-/Bildflaechen und notwendige Feinanpassungen erlaubt.
- Icons kommen aus MudBlazor/Material Icons, sofern kein zwingender Produktgrund fuer eigene SVGs besteht.

## Design Tokens

### Farben

| Token | Dunkel | Hell | Verwendung |
|---|---:|---:|---|
| `--mcs-bg` | `#07070a` | `#f6f1e8` | App-Hintergrund |
| `--mcs-bg-soft` | `#101016` | `#efe5d5` | Seitenflaechen, AppBar, Bottom-Bar |
| `--mcs-surface` | `#171720` | `#fff9ef` | Cards, Panels, Drawer |
| `--mcs-surface-raised` | `#20202b` | `#ffffff` | aktive Flaechen, Dialoge |
| `--mcs-border` | `#343442` | `#d7cbb8` | Hairlines, Trenner, Input-Border |
| `--mcs-text` | `#f5f1e8` | `#211b12` | Primaerer Text |
| `--mcs-text-muted` | `#b8b2a7` | `#635b4e` | Sekundaerer Text, Hilfetext |
| `--mcs-text-disabled` | `#77727f` | `#9b907f` | Disabled, Platzhalter |
| `--mcs-gold` | `#d8a83f` | `#9a6d13` | Primaeraktion, Scan-Fokus, aktive Navigation |
| `--mcs-gold-strong` | `#f2c35b` | `#6f4c08` | Hover/Highlight, wichtige Statuspunkte |
| `--mcs-gold-soft` | `#3a2b12` | `#f3dfb4` | dezente Goldflaechen |
| `--mcs-primary-contrast` | `#120f08` | `#fff9ef` | Text auf Primaeraktionen |
| `--mcs-red` | `#ff5a5f` | `#b3261e` | Fehler, kritische Hinweise |
| `--mcs-error-bg` | `#5b1518` | `#f8d7d4` | Fehlerflaechen |
| `--mcs-error-contrast` | `#ffffff` | `#3d0b08` | Text auf Fehlerflaechen |
| `--mcs-green` | `#49d17d` | `#247a45` | Erfolg, bereit, gespeichert |
| `--mcs-blue` | `#64b5f6` | `#1e6aa8` | Info, technische Hinweise |
| `--mcs-media-bg` | `#000000` | `#000000` | Kamera-/Bildflaechen |
| `--mcs-media-bg-soft` | `#050507` | `#050507` | vorbereitete Bildflaechen |
| `--mcs-media-text` | `#f5f1e8` | `#f5f1e8` | Text auf dunklen Medienflaechen |
| `--mcs-bottom-bar-bg` | `rgba(16, 16, 22, 0.96)` | `rgba(255, 249, 239, 0.96)` | mobile Bottom-Bar |
| `--mcs-camera-overlay` | `rgba(0, 0, 0, 0.58)` | `rgba(0, 0, 0, 0.58)` | Kamera-Abdunklung |
| `--mcs-glow-gold` | `rgba(216, 168, 63, 0.16)` | `rgba(154, 109, 19, 0.12)` | dezente Fokusverlaeufe |
| `--mcs-glow-gold-strong` | `rgba(216, 168, 63, 0.22)` | `rgba(154, 109, 19, 0.18)` | staerkere Fokusverlaeufe |
| `--mcs-gold-border` | `rgba(216, 168, 63, 0.34)` | `rgba(154, 109, 19, 0.26)` | Gold-Hairlines |
| `--mcs-gold-border-strong` | `rgba(216, 168, 63, 0.42)` | `rgba(154, 109, 19, 0.38)` | starke Gold-Hairlines |

Regeln:

- Primaerfarbe ist Gold, nicht Blau.
- Default ist Dunkel. Helle Vollseiten sind erlaubt, wenn sie denselben Werkzeugcharakter behalten und nicht nach Marketing- oder Admin-Oberflaeche wirken.
- Kamera- und Medienflaechen duerfen auch im hellen Design dunkel bleiben.
- Statusfarben werden sparsam eingesetzt und duerfen Gold nicht ersetzen.
- Textkontrast muss auf echten Smartphone-Displays bei geringer Helligkeit lesbar bleiben.

### Spacing

Basis ist ein 4px-Raster.

| Token | Wert | Verwendung |
|---|---:|---|
| `--mcs-space-1` | `4px` | feine Abstaende |
| `--mcs-space-2` | `8px` | Icon/Text, kompakte Gruppen |
| `--mcs-space-3` | `12px` | kleine Innenabstaende |
| `--mcs-space-4` | `16px` | Standard-Padding mobil |
| `--mcs-space-5` | `20px` | Formulargruppen |
| `--mcs-space-6` | `24px` | Cards, Seitenabschnitte |
| `--mcs-space-8` | `32px` | groessere Bloecke |
| `--mcs-space-10` | `40px` | Desktop-Abschnitte |

Regeln:

- Mobile Seiten haben horizontal `16px` Padding.
- Primaeraktionen liegen in Daumennaehe am unteren Rand.
- Vertikale Abstaende sind kompakt; die App ist ein Werkzeug, keine Landingpage.

### Radius

| Token | Wert | Verwendung |
|---|---:|---|
| `--mcs-radius-xs` | `6px` | Badges, kleine Markierungen |
| `--mcs-radius-sm` | `10px` | Inputs, kleine Buttons |
| `--mcs-radius-md` | `14px` | Cards, Panels, Menus |
| `--mcs-radius-lg` | `20px` | Kamera-Preview, grosse Cards |
| `--mcs-radius-pill` | `999px` | Chips, Bottom-Actions |

Regeln:

- Keine eckigen Standard-Container.
- Keine uebertrieben weichen Marketing-Karten.
- Kamera- und Bildflaechen bekommen den groessten Radius.

### Typografie

System-Font-Stack: `Inter, Segoe UI, Roboto, Arial, sans-serif`. Keine extern geladenen Fonts.

| Token | Groesse | Gewicht | Zeilenhoehe | Verwendung |
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
- Zahlen, Status und Scan-Ergebnisse muessen sofort erfassbar sein.

### Touch, Hoehen und Bewegung

- Mindest-Touchziel: `48px` Hoehe und Breite.
- Primaerbutton mobil: `56px` Hoehe.
- Bottom-Action-Bar: `72px` Mindesthoehe plus Safe-Area.
- AppBar mobil: `56px`, Desktop: `64px`.
- Animationen: `120ms` bis `180ms`, easing `ease-out`.
- Keine langen Parallax-, Marketing- oder Scroll-Animationen.

## MudBlazor-Einschraenkungen

- `MudTheme` bildet die Tokens ab; keine verstreuten Hex-Werte in Komponenten.
- `MudButton` nutzt `Variant.Filled` fuer Primaeraktionen und `Variant.Outlined` oder `Variant.Text` fuer Nebenaktionen.
- `Color.Primary` ist Gold. `Color.Secondary` bleibt dunkel/dezent.
- `MudCard` ist fuer strukturierte Inhalte erlaubt, aber nicht fuer jede kleine Textgruppe.
- `MudPaper` darf fuer App-Shell-, Kamera- und Einstellungs-Panels genutzt werden.
- `MudDialog` nur fuer echte Unterbrechungen: Berechtigungen, Loeschen, kritische Fehler.
- `MudSnackbar` nur fuer kurze Rueckmeldungen: gespeichert, Fehler, offline, Upload bereit.
- `MudDrawer` auf Desktop erlaubt; mobil keine dauerhafte Seitenleiste.
- `MudGrid` ist fuer einfache Raster erlaubt; fuer Smartphone-Flows bevorzugt einspaltige Flex-/Stack-Layouts.
- `MudTable` ist mobil zu vermeiden; Ergebnisse als Cards oder Listen darstellen.
- Keine Inline-Styles ausser dynamischen, komponentennahen Werten wie Bildgroessen aus Laufzeitdaten.

## Layoutvorlagen

### `app-shell`

Zweck: globale PWA-Huelle.

- Hintergrund `--mcs-bg` ueber die gesamte Viewport-Hoehe.
- `MudAppBar` flach, mit Logo/Titel links und optionaler Statusaktion rechts.
- Desktop darf `MudDrawer` fuer Navigation nutzen.
- Mobile Navigation wird als Bottom-Navigation oder Bottom-Actions umgesetzt, nicht als permanenter Drawer.
- Content beruecksichtigt `safe-area-inset-top` und `safe-area-inset-bottom`.

### `mobile-bottom-action`

Zweck: feste Hauptaktion fuer Daumenbedienung.

- Am unteren Rand fixiert oder sticky.
- Hintergrund `--mcs-bg-soft` mit oberer Hairline `--mcs-border`.
- Primaeraktion als goldener `MudButton` mit `56px` Hoehe und Pill-Radius.
- Nebenaktionen links/rechts nur, wenn sie im Flow wirklich gebraucht werden.
- Muss `env(safe-area-inset-bottom)` einrechnen.

### `mobile-page`

Zweck: Standardseite fuer Smartphone.

- Einspaltig, max. Breite `520px`, zentriert auf groesseren Screens.
- Padding mobil `16px`, Desktop `24px` bis `32px`.
- Seitenkopf: kurzer Titel, optional ein Satz Kontext.
- Inhalt in klaren Abschnitten mit `24px` Abstand.
- Hauptaktion unten, nicht versteckt in der Kopfzeile.

### `camera-flow`

Zweck: Foto aufnehmen, Bild laden, Scan vorbereiten.

- Kamera-/Bildbereich ist die visuelle Mitte der Seite.
- Preview als dunkles Panel mit Radius `20px`, Hairline und optionaler Gold-Fokusmarke.
- Overlay-Hinweise kurz: z. B. `Hand ruhig halten`, `Muenze sichtbar platzieren`.
- Primaeraktion: `Foto aufnehmen` oder `Bild verwenden`.
- Sekundaeraktionen: `Aus Galerie laden`, `Erneut aufnehmen`, `Abbrechen`.
- Berechtigungsfehler zeigen konkrete naechste Schritte, keinen generischen Fehlertext.

### `settings`

Zweck: Einstellungen ohne Ablenkung.

- Gruppen als `MudPaper`/`MudCard` auf `--mcs-surface`.
- Jede Gruppe hat Titel, optional Hilfetext, dann Controls.
- Toggles und Selects muessen grosse Touchziele behalten.
- Gefaehrliche Aktionen stehen am Ende und nutzen Rot nur fuer die konkrete Aktion.

### `placeholder`

Zweck: leere, kommende oder nicht verfuegbare Zustaende.

- Card mit dezentem Icon, kurzem Titel und einem hilfreichen Satz.
- Wenn moeglich eine konkrete Aktion anbieten.
- Keine generischen Illustrationen, keine Maskottchen, keine Marketinggrafiken.
- Offline-/Berechtigungs-/Kein-Bild-Zustaende muessen eindeutig unterscheidbar sein.

## Komponentenregeln

- Primaerbuttons sind gold, breit und unten erreichbar.
- Sekundaerbuttons sind outlined oder textbasiert.
- Inputs sind klar beschriftet und nicht nur ueber Placeholder erklaert.
- Cards trennen Funktionen, nicht Dekoration.
- Badges zeigen Status wie `Bereit`, `Offline`, `Demo`, `Fehler`.
- Icons unterstuetzen Text, ersetzen ihn aber nicht bei wichtigen Aktionen.
- Loading States zeigen, was passiert: `Bild wird vorbereitet`, `Scan laeuft`, `Wird gespeichert`.

## Do

- Smartphone zuerst entwerfen und dann fuer Desktop erweitern.
- Dunkles Design als Default konsequent halten; helles Design bleibt ruhig, warm und werkzeughaft.
- Gold nur fuer Fokus, Fortschritt und primaere Aktionen verwenden.
- Kamera- und Bildflaechen gross, ruhig und kontrastreich darstellen.
- Deutsche, kurze, aktive Beschriftungen verwenden.
- Offline- und Berechtigungszustaende als normale PWA-Zustaende behandeln.
- MudBlazor-Komponenten bevorzugen und nur gezielt stylen.

## Don't

- Keine Clay.com-, SaaS-Marketing-, Cream-Canvas- oder 3D-Maskottchen-Aesthetik.
- Keine Bootstrap-Klassen oder zweite UI-Bibliothek.
- Keine hellgrauen Admin-Oberflaechen und keine beliebige SaaS-Marketing-Aesthetik.
- Keine Navigation, die auf Mobile wichtige Aktionen nach oben oder in Menues versteckt.
- Keine langen Texte in Buttons oder Kamera-Overlays.
- Keine Tabellen fuer mobile Scan-Ergebnisse.
- Keine Hover-only Interaktionen; Touch muss vollstaendig funktionieren.
- Keine neuen Farben, Abstaende oder Radien ohne Token-Erweiterung in diesem Dokument.

## Umsetzungsreihenfolge

1. `MudTheme` mit Farb-, Typografie-, Radius- und Default-Komponentenwerten definieren.
2. `app-shell` auf dunkle PWA-Huelle, Safe-Areas und mobile Navigation bringen.
3. `mobile-page` und `mobile-bottom-action` als wiederverwendbare Struktur etablieren.
4. `camera-flow` fuer Aufnahme, Galerie, Preview und Berechtigungen gestalten.
5. `settings` und `placeholder` vereinheitlichen.
6. Bestehende Seiten auf Tokens, MudBlazor-only und deutsche Microcopy pruefen.
7. Visuelle Sonderfaelle entfernen: Inline-Hex, Bootstrap-Reste, helle Marketing-Flaechen.

## Verifikation

- `DESIGN.md` ist die Quelle fuer UI-Entscheidungen; Abweichungen muessen bewusst begruendet werden.
- Suche nach Bootstrap-Klassen und fremden UI-Bibliotheken muss ohne neue Treffer bleiben.
- Suche nach Inline-Hex-Werten in Komponenten muss begruendet oder bereinigt sein.
- Build, Lint und Tests muessen nach UI-Aenderungen laufen, sofern im Projekt vorhanden.
- Manuelle Pruefung auf einem Smartphone-Viewport: `360x800`, `390x844`, `430x932`.
- Touchziele mindestens `48px`; Hauptaktion unten erreichbar.
- Dark-Mode-Kontrast bei niedriger Displayhelligkeit pruefen.
- PWA-Zustaende pruefen: offline, fehlende Kamera-Berechtigung, kein Bild, Fehler, Erfolg.
