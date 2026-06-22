# Training-FAQ fuer Anwender

Diese FAQ beschreibt den praktischen Ablauf vom Sammeln der Rohbilder bis zum Modell in der PWA. Sie richtet sich an Anwender mit grundlegendem IT-Know-how, aber ohne Spezialwissen zu Modellen oder Bildverarbeitung.

## Kurzueberblick

Der Trainer lernt nicht "eine Muenze auswendig", sondern wo auf einem Foto die Muenze ist. Dafuer braucht er viele Beispielbilder und zu jedem Bild eine Maske. Die Maske sagt: Diese Pixel gehoeren zur Muenze, alle anderen Pixel sind Hintergrund.

Der typische Ablauf ist:

1. Rohbilder mit der PWA sammeln.
2. Raw-ZIP aus der PWA exportieren.
3. Raw-ZIP im Desktop-Trainer importieren.
4. Pro Bild die Muenze sauber maskieren.
5. Daten pruefen.
6. Daten in Training, Validierung und Test aufteilen.
7. Modell trainieren.
8. Modell testen.
9. ONNX exportieren.
10. Modellpaket erstellen.
11. Modell in die PWA uebernehmen.
12. Modell in den PWA-Einstellungen auswaehlen.

## Wieviele Bilder brauche ich?

### Reicht eine kleine Bildmenge?

Fuer einen ersten Funktionstest reichen oft 50 bis 100 sauber maskierte Bilder. Damit prueft man, ob der Workflow funktioniert. Fuer ein brauchbares Modell sind mehr Bilder noetig.

Praxiswerte:

| Ziel | Gesamtbilder | Train | Val | Test |
|---|---:|---:|---:|---:|
| Workflow-Test | 50-100 | ca. 80% | ca. 10% | ca. 10% |
| Erstes brauchbares Modell | 200-400 | ca. 80% | ca. 10% | ca. 10% |
| Robusteres Modell | 500-1000+ | ca. 80% | ca. 10% | ca. 10% |

Wichtig: 200 gute, abwechslungsreiche und korrekt maskierte Bilder sind besser als 1000 sehr aehnliche oder falsch maskierte Bilder.

### Was sind Train, Val und Test?

- `Train`: Bilder, aus denen das Modell lernt.
- `Val`: Bilder, mit denen der Trainer waehrend des Trainings prueft, ob das Modell besser wird.
- `Test`: Bilder, die erst nach dem Training fuer eine ehrliche Endkontrolle verwendet werden.

Die GUI-Aktion **Daten aufteilen** erzeugt standardmaessig ungefaehr 80% Training, 10% Validierung und 10% Test.

### Wieviele Testbilder sind sinnvoll?

Der Test-Split sollte nicht leer sein. Fuer erste Versuche sind 10 bis 20 Testbilder akzeptabel. Besser sind mindestens 30 bis 50 Testbilder, besonders wenn es verschiedene Hintergruende, Lichtarten oder Muenzen gibt.

## Wie sollen die Rohbilder aussehen?

### Wie gross soll die Muenze im Bild sein?

Die Muenze sollte deutlich sichtbar sein. Als Faustregel sollte sie ungefaehr 40% bis 80% der Bildhoehe oder Bildbreite einnehmen. Sie darf nicht abgeschnitten sein.

Gut:

- Muenze vollstaendig im Bild.
- Rand der Muenze klar sichtbar.
- Einige Bilder nah dran, einige mit etwas mehr Umgebung.
- Unterschiedliche reale Abstaende, aber keine winzige Muenze in einer grossen Szene.

Schlecht:

- Muenze ist nur ein kleiner Punkt im Bild.
- Muenze ist am Rand abgeschnitten.
- Starker digitaler Zoom mit matschigen Details.
- Bild ist unscharf oder verwackelt.

### Welche Belichtung ist gut?

Das Modell soll spaeter reale Fotos verarbeiten. Deshalb braucht es reale Lichtvarianten, aber keine unbrauchbaren Bilder.

Gut:

- Gleichmaessiges Licht.
- Einige Bilder mit hellerer und dunklerer Umgebung.
- Leichte Schatten, wenn sie in der echten Nutzung vorkommen.
- Keine komplett ueberstrahlten Muenzen.

Schlecht:

- Glanz so stark, dass grosse Teile der Muenze weiss ausbrennen.
- Muenze ist fast schwarz.
- Harte Schatten verdecken den Rand.
- Farbige Lichter, die nicht zur spaeteren Nutzung passen.

### Welche Winkel sind sinnvoll?

Die Muenze sollte meistens frontal oder leicht schraeg fotografiert werden. Einige Winkelvarianten sind gut, weil die PWA spaeter nicht immer perfekte Bilder bekommt.

Gut:

- Frontal von oben.
- Leicht schraeg aus mehreren Richtungen.
- Verschiedene Rotationen der Muenze.

Schlecht:

- Extrem flacher Winkel, bei dem die Muenze wie eine schmale Ellipse wirkt.
- Teile der Muenze verschwinden hinter Fingern oder Objekten.

### Hand, Tisch oder Palm als Hintergrund?

Hand, Palm oder Tisch sind als Hintergrund okay. Wichtig ist, dass sie Hintergrund bleiben und nicht als Muenze maskiert werden.

Regeln:

- Keine Finger auf der Muenzflaeche.
- Eine offene Handflaeche oder Palm hinter der Muenze ist okay.
- Finger am Rand sind nur dann akzeptabel, wenn sie die Muenzflaeche nicht verdecken.
- Wenn ein Finger auf der Muenze liegt, Bild ausschliessen oder neu aufnehmen.
- Tisch, Matte, Papier oder Hand sind gute Hintergruende, wenn der Muenzrand erkennbar bleibt.

### Was ist mit Sharpie-Markierungen?

Eine Sharpie-Markierung auf der Muenze gehoert zur Muenze. Sie darf nicht ausgeschnitten werden.

Maskierungsregel:

- Markierung auf der Muenze = Muenze.
- Die Maske umfasst die komplette sichtbare Muenze inklusive Markierung.
- Nicht versuchen, die Markierung als Fehler oder Hintergrund zu entfernen.

## Wie maskiere ich perfekt in der Anwendung?

### Was bedeutet Maskieren?

Maskieren bedeutet: Du markierst genau den Bildbereich, der zur sichtbaren Muenze gehoert. Alles andere bleibt Hintergrund.

Die gespeicherte Maske ist technisch eine Schwarz-Weiss-Datei:

- Weiss (`255`) = Muenze.
- Schwarz (`0`) = Hintergrund.

### Was gehoert in die Maske?

In die Maske gehoert:

- Die komplette sichtbare Muenzflaeche.
- Der sichtbare Muenzrand.
- Praegung, Schmutz, Kratzer und Verfaerbungen auf der Muenze.
- Sharpie-Markierungen auf der Muenze.

Nicht in die Maske gehoert:

- Finger, Hand, Palm oder Tisch.
- Schatten neben der Muenze.
- Spiegelungen ausserhalb der Muenze.
- Etiketten, Papier, Messhilfen oder andere Objekte.

### Wie arbeite ich am besten in der GUI?

1. Bild oeffnen und auf die Muenze zoomen.
2. Falls passend, mit dem Ellipse-Werkzeug eine grobe Startform setzen.
3. Mit Pinsel fehlende Muenzbereiche ergaenzen.
4. Mit Radierer uebermalten Hintergrund entfernen.
5. Den Rand bei hoher Zoomstufe kontrollieren.
6. Maske speichern.
7. Bei schlechten Bildern lieber **Bild ausschliessen** als eine fragwuerdige Maske erzwingen.

Nuetzliche Bedienung:

- `Strg` + Mausrad: zoomen.
- Pinsel: Muenze hinzufuegen.
- Radierer: Hintergrund entfernen.
- Ellipse: schnelle Grundform fuer runde Muenzen.
- `[` und `]`: Pinselradius kleiner/groesser.
- `Strg+Z`: Rueckgaengig.

### Wie genau muss der Rand sein?

Der Rand ist der wichtigste Bereich. Das Modell lernt dort, wo die Muenze endet und der Hintergrund beginnt. Kleine Fehler sind nicht dramatisch, aber systematische Fehler schaden.

Gut:

- Maske liegt moeglichst genau auf dem sichtbaren Muenzrand.
- Keine Loecher innerhalb der Muenze.
- Keine grossen Hintergrundbereiche an der Muenze klebend.

Schlecht:

- Rand wird regelmaessig zu klein maskiert.
- Rand wird regelmaessig zu gross maskiert.
- Schatten wird als Teil der Muenze markiert.
- Finger auf der Muenze werden mitmaskiert.

## Was ist der generelle Workflow vom Raw-ZIP bis zur Modelluebertragung?

### Schritt 1: Rohbilder sammeln

In der PWA den Expertenmodus aktivieren und Rohbilder sammeln. Achte bereits hier auf gute Bildqualitaet, klare Muenzraender und keine Finger auf der Muenzflaeche.

### Schritt 2: Raw-ZIP exportieren

Die PWA exportiert eine Raw-ZIP mit Bildern und `metadata.json`. Diese ZIP bleibt das Original und sollte unveraendert archiviert werden, zum Beispiel unter `trainer/data/incoming/`.

### Schritt 3: Raw-ZIP importieren

In der Trainer-GUI **Raw-ZIP importieren** ausfuehren. Der Trainer legt daraus ein Dataset an und bereitet leere Masken vor.

### Schritt 4: Bilder maskieren

Jedes geeignete Bild wird maskiert. Schlechte oder unbrauchbare Bilder werden ausgeschlossen.

### Schritt 5: Daten pruefen

Mit **Daten pruefen** kontrolliert der Trainer, ob Bilder, Masken und Metadaten zusammenpassen. Fehler muessen behoben werden, bevor trainiert wird.

### Schritt 6: Daten aufteilen

Mit **Daten aufteilen** erzeugt der Trainer `train.txt`, `val.txt` und `test.txt`. Ausgeschlossene Bilder werden nicht verwendet.

### Schritt 7: Training starten

Mit **Training starten** wird ein Trainingslauf erzeugt, zum Beispiel unter `trainer/runs/coinseg/general-001/`. Der Trainer speichert Checkpoints und Metriken.

### Schritt 8: Modell testen

Mit **Modell testen** wird das Modell auf den Testbildern bewertet. Gute Werte sind hilfreich, ersetzen aber nicht die Sichtpruefung in der PWA.

### Schritt 9: ONNX exportieren

Mit **ONNX exportieren** wird das Modell in ein Format gebracht, das die PWA im Browser laden kann.

### Schritt 10: Modellpaket erstellen

Mit **Modellpaket erstellen** wird ein Paket mit Modell, Metadaten und Vorverarbeitungsbeschreibung erzeugt.

### Schritt 11: Modell in PWA uebernehmen

Mit **Modell in PWA uebernehmen** kopiert die GUI das Modell nach `wwwroot/models/<model-id>/` und aktualisiert `wwwroot/models/manifest.json`.

### Schritt 12: Modell in der PWA auswaehlen

In der PWA unter **Einstellungen** das Scan-Modell auswaehlen. Wenn kein gueltiges Modell im Manifest steht, nutzt die PWA die lokale Heuristik.

## Wie gehe ich mit mehreren Trainings-ZIP-Dateien von mehreren Helfern um?

### Kann ich mehrere Raw-ZIPs einfach nacheinander importieren?

Ja, aber nur sicher, wenn die Dataset-IDs unterschiedlich sind. Der Import legt Datasets anhand der `datasetId` an. Wenn zwei ZIP-Dateien dieselbe `datasetId` haben, koennen vorhandene Daten ueberschrieben oder ersetzt werden.

Praxisregel:

- Original-ZIPs immer unveraendert archivieren.
- Jede ZIP vor dem Import eindeutig benennen, zum Beispiel `helfer-anna-session-2026-06-22.zip`.
- Nach dem Import pruefen, welches Dataset entstanden ist.
- Keine zweite ZIP mit gleicher `datasetId` importieren, solange das erste Dataset nicht gesichert/exportiert ist.

### Wie organisiere ich mehrere Helfer?

Bewaehrter Ablauf:

1. Jeder Helfer sammelt eine eigene Session.
2. Jede Session wird als eigene Raw-ZIP abgelegt.
3. Jede Raw-ZIP wird als eigenes Dataset importiert.
4. Jedes Dataset wird separat maskiert und geprueft.
5. Nach der Annotation werden die Datasets als annotated ZIP exportiert und archiviert.
6. Erst danach wird entschieden, ob ein gemeinsames Trainingsdataset manuell zusammengefuehrt wird.

Der Trainer hat aktuell keinen Komfort-Button fuer automatisches Zusammenfuehren mehrerer annotierter Datasets. Wenn Datasets manuell kombiniert werden, muessen Bilddateien, Maskendateien und `metadata.json` konsistent bleiben. Sample-IDs und Dateinamen duerfen nicht kollidieren.

### Was soll ich Helfern vorgeben?

Gib Helfern einfache Regeln:

- 50 bis 150 Bilder pro Session sind gut handhabbar.
- Unterschiedliche Hintergruende und Lichtbedingungen aufnehmen.
- Keine Finger auf der Muenzflaeche.
- Muenze nicht abschneiden.
- Verwackelte oder stark ueberstrahlte Bilder vermeiden.
- Bei Sharpie-Markierungen: Markierung sichtbar lassen, nicht verstecken.

## Do's and Don'ts

### Do's

- Gute Rohbilder sammeln, bevor viel Zeit in Masken fliesst.
- Muenze vollstaendig sichtbar aufnehmen.
- Verschiedene Hintergruende verwenden, wenn sie spaeter real vorkommen.
- Unterschiedliche Winkel und Beleuchtungen aufnehmen.
- Pro Bild nur die sichtbare Muenze maskieren.
- Sharpie-Markierungen als Teil der Muenze behandeln.
- Schlechte Bilder ausschliessen.
- Nach dem Maskieren immer **Daten pruefen** ausfuehren.
- Modelle mit klarer ID und Version benennen.
- Original-ZIPs und exportierte annotated Datasets archivieren.

### Don'ts

- Keine Finger auf der Muenzflaeche fotografieren.
- Keine abgeschnittenen Muenzen trainieren, wenn sie spaeter nicht gewuenscht sind.
- Keine Schatten oder Tischflaechen mitmaskieren.
- Keine Sharpie-Markierung aus der Maske herausschneiden.
- Keine stark verwackelten Bilder verwenden.
- Nicht nur fast identische Bilder trainieren.
- Testbilder nicht nachtraeglich zum Training hinzufuegen, wenn sie fuer die Endkontrolle gedacht sind.
- Nicht mehrere Helfer-ZIPs mit gleicher `datasetId` unkontrolliert importieren.
- Nicht einfach Modellordner loeschen, ohne das Manifest zu aktualisieren.

## Was bedeuten die Felder beim Modell?

Beim Erstellen oder Uebernehmen eines Modells fragt die GUI Modelldaten ab. Diese Daten landen in `model.json` und im Manifest.

| Feld | Bedeutung | Empfehlung |
|---|---|---|
| `ID` / `model-id` | Technischer eindeutiger Name. Wird auch Ordnername unter `wwwroot/models/<model-id>/`. | Kurz, eindeutig, klein geschrieben, z. B. `coin-general-001`. |
| `Anzeigename` / `displayName` | Name, den Anwender in der PWA sehen. | Verstaendlich, z. B. `Coin General 001`. |
| `Beschreibung` | Kurzer Hinweis zum Zweck des Modells. | Datensatz, Licht oder Muenztyp nennen. |
| `Objekttyp` / `objectType` | Was segmentiert wird. | Fuer Muenzen normalerweise `coin`. |
| `Waehrung` / `currency` | Optionale Einordnung der Muenzen. | `unknown`, `EUR`, `USD` oder projektbezogen. |
| `Einsatz` / `useCase` | Wofuer das Modell verwendet wird. | Normalerweise `segmentation`. |
| `Profil` / `profile` | Trainingsprofil bzw. Modellfamilie. | `general`, `poker-coins`, `silver-dollar`, `stage-light` oder `customer-*`. |
| `Version` | Versionsnummer dieses Modells. | Semantisch oder laufend, z. B. `0.6.0` oder `1.0.0`. |
| `Modell-ID` | Oft gleichbedeutend mit `ID`. | Muss eindeutig im Manifest sein. |

### Naming-Beispiele

Gute IDs:

- `coin-general-001`
- `poker-coins-stage-001`
- `customer-acme-eur-002`
- `silver-dollar-strong-light-001`

Unguenstig:

- `test`
- `neu`
- `final-final`
- `Modell Anna fertig!!!`

Die technische ID wird bereinigt. Trotzdem sollte sie direkt sauber gewaehlt werden: keine Leerzeichen, keine Sonderzeichen, keine wechselnde Gross-/Kleinschreibung.

## Was bedeuten Letterbox, Maske, ONNX und Manifest?

### Letterbox

Letterbox bedeutet: Das Bild wird so verkleinert oder vergroessert, dass es in ein festes Quadrat passt, ohne verzerrt zu werden. Freie Raender werden aufgefuellt. In diesem Projekt ist das Zielformat `512x512`.

Einfach gesagt: Die Muenze bleibt rund und wird nicht breitgezogen.

### Maske

Eine Maske ist ein Schwarz-Weiss-Bild zum Originalfoto. Weiss markiert die Muenze, Schwarz markiert Hintergrund. Aus diesen Masken lernt das Modell.

### ONNX

ONNX ist das Austauschformat fuer das trainierte Modell. Der Trainer trainiert mit Python/PyTorch, die PWA laedt spaeter eine `.onnx`-Datei im Browser.

Einfach gesagt: ONNX ist die transportierbare Modell-Datei.

### Manifest

Das Manifest ist eine Liste der verfuegbaren Modelle. Es liegt unter `wwwroot/models/manifest.json`. Die PWA liest diese Liste und zeigt die Modelle in den Einstellungen an.

Ein Modell besteht typischerweise aus:

```text
wwwroot/models/<model-id>/
  coin-segmentation.onnx
  model.json
  metrics.json
  preprocessing.json
```

## Wie loesche ich Modelle?

### Kann ich Modelle direkt in der PWA loeschen?

Nein. Die PWA bietet aktuell eine Auswahl verfuegbarer Modelle, aber keine Loeschfunktion fuer gebuendelte Projektdateien. Wenn kein Modell verfuegbar ist, nutzt die PWA die lokale Heuristik.

### Wie loesche ich ein Modell im Projekt?

Modelle werden im Projekt unter `wwwroot/models/` verwaltet. Zum Entfernen eines Modells:

1. Ordner `wwwroot/models/<model-id>/` loeschen.
2. Eintrag mit derselben `id` aus `wwwroot/models/manifest.json` entfernen.
3. Falls `defaultModelId` auf dieses Modell zeigt, `defaultModelId` auf ein anderes Modell setzen oder auf `null` setzen.
4. Projekt neu bauen oder neu ausliefern.
5. PWA im Browser aktualisieren. Bei installierter PWA ggf. Cache/Service-Worker-Aktualisierung beachten.

Nicht ausreichend:

- Nur den Ordner loeschen, aber den Manifest-Eintrag stehen lassen.
- Nur den Manifest-Eintrag loeschen, aber alte Dateien unkontrolliert liegen lassen.

### Kann ich Trainingslaeufe und Modellpakete loeschen?

Ja, aber sie haben unterschiedliche Rollen:

- `trainer/runs/`: Trainingslaeufe, Checkpoints und Metriken. Loeschen spart Platz, nimmt aber die Moeglichkeit, denselben Run erneut zu exportieren.
- `trainer/model-packages/`: exportierte ZIP-Pakete. Loeschen entfernt nur das Archiv, nicht automatisch das PWA-Modell.
- `wwwroot/models/`: Modelle, die die PWA tatsaechlich verwenden kann.

Vor dem Loeschen produktiver Modelle immer eine Sicherung behalten.

## Checkliste vor dem Training

- Genug Bilder vorhanden, idealerweise mindestens 200 fuer ein erstes brauchbares Modell.
- Muenze ist nicht abgeschnitten.
- Keine Finger liegen auf der Muenzflaeche.
- Hand/Palm/Tisch sind nur Hintergrund.
- Sharpie-Markierungen auf der Muenze sind mitmaskiert.
- Schlechte Bilder sind ausgeschlossen.
- Masken haben saubere Raender.
- **Daten pruefen** ist ohne Fehler durchgelaufen.
- **Daten aufteilen** wurde ausgefuehrt.
- Modell-ID, Profil und Version sind sinnvoll gewaehlt.

## Checkliste vor der PWA-Uebernahme

- Training ist abgeschlossen.
- Modell wurde getestet.
- ONNX-Export war erfolgreich.
- Modellpaket wurde erstellt.
- `model-id` ist eindeutig.
- Bestehende Modelle werden nicht versehentlich ersetzt.
- Nach der Uebernahme steht das Modell in `wwwroot/models/manifest.json`.
- In der PWA ist das Modell unter **Einstellungen** auswaehlbar.
