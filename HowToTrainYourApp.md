# How To Train Your App

Diese Anleitung erklärt den neuen Trainingsablauf für MagicCoinSnapper.

Kurz gesagt: Das Smartphone sammelt Bilder. Der Desktop macht die genaue Markierung. Das Modell entsteht danach lokal im Trainingsworkflow.

## Warum der Ablauf getrennt ist

Auf dem Smartphone ist die App fuer die Vorfuehrung gedacht: schnell, dunkel, einhaendig bedienbar und offline.

Masken sauber zu zeichnen ist dort aber unpraktisch. Mit Maus, großem Bildschirm und Tastatur geht das deutlich besser. Darum wird die Arbeit getrennt:

- Smartphone: Rohbilder sammeln.
- Desktop-Trainer: Bilder sichten, Münze markieren, Metadaten pflegen.
- Trainingspipeline: Modell trainieren, testen und als ONNX exportieren.
- PWA: fertiges Modell in den Einstellungen für den Scan auswählen.

## Was bedeutet Training jetzt?

Training bedeutet nicht, dass die PWA selbst auf dem Smartphone rechnet und lernt.

Die PWA liefert nur gute Beispielbilder. Auf dem Desktop entstehen daraus saubere Trainingsdaten: Bild plus Maske plus Metadaten.

Aus diesen Trainingsdaten wird ein Modell gebaut. Dieses Modell wird später vom Trainer in die App übernommen oder als Modellpaket bereitgestellt.

## Was ist eine Maske?

Eine Maske markiert die Münze im Bild.

Alles innerhalb der Maske gehört zur Münze. Alles außerhalb wird beim späteren Scan transparent.

Diese Maske zeichnest Du nicht mehr auf dem Smartphone, sondern im Desktop-Trainer.

## Schritt 1: Expertenmodus aktivieren

1. Öffne MagicCoinSnapper.
2. Gehe zu **Einstellungen**.
3. Aktiviere **Bildersammlung anzeigen**.
4. Im Menue erscheint **Bildersammlung**.

Der Schalter ist lokal. Er gilt nur auf diesem Gerät und nur in diesem Browser.

## Schritt 2: Rohbilder sammeln

1. Gehe zu **Scan**.
2. Nimm ein Bild auf oder lade ein Bild aus der Galerie.
3. Öffne **Bildersammlung**.
4. Tippe auf **Aktuelles Scanbild verwenden**.
5. Fuege optional eine kurze Notiz hinzu.
6. Tippe auf **Rohbild speichern**.
7. Wiederhole das mit mehreren Bildern.

Du kannst in der Bildersammlung auch direkt ein Bild aus der Galerie laden.

## Schritt 3: Raw-ZIP exportieren

1. Öffne **Bildersammlung**.
2. Pruefe die Anzahl der gesammelten Rohbilder.
3. Tippe auf **Raw-ZIP exportieren**.
4. Die ZIP-Datei landet im Download- oder Dateien-Bereich Deines Smartphones.
5. Diese Datei kannst Du manuell weitergeben, zum Beispiel per E-Mail, Upload, Messenger oder Kabel.

Die PWA verschickt nichts automatisch.

## Was steckt im Raw-ZIP?

Das ZIP ist fuer den Desktop-Trainer gedacht.

```text
mcs-raw-images-2026-06-20.zip
  images/
    sample-0001.jpg
    sample-0002.png
  metadata.json
```

Die `metadata.json` beschreibt die Bilder und enthält Notizen, Quelle, Größe und Zeitpunkt.

## Schritt 4: Auf dem Desktop markieren

Der Desktop-Trainer importiert das Raw-ZIP.

Dort kannst Du:

- Bilder durchblättern.
- Reinzoomen.
- Die Münze mit Maus oder Stift markieren.
- Fehler schnell korrigieren.
- Bilder ausschliessen.
- Metadaten pflegen.
- Trainingsgruppen setzen.
- Daten prüfen und aufteilen.
- Training starten und Modell testen.
- ONNX exportieren, Modellpaket erstellen und das Modell in die PWA übernehmen.

Das ist der richtige Ort fuer genaue Maskenarbeit.

## Welche Metadaten sind sinnvoll?

Metadaten helfen später, verschiedene Modelle zu trainieren.

Beispiele:

- Münze in Hand.
- Filzuntergrund.
- Pokermünze.
- Silberdollar.
- Bühnenlicht.
- Sharpie-Markierung sichtbar.
- Schwieriger Fall.
- Fuer allgemeines Modell geeignet.
- Fuer Spezialmodell geeignet.

Damit kannst Du später gezielt trainieren: allgemein, nur Pokermünzen, nur eine bestimmte Münze oder nur eine bestimmte Show-Situation.

## Allgemeines Modell oder Spezialmodell?

Ein allgemeines Modell soll für viele Anwender funktionieren. Dafür braucht es viele unterschiedliche Bilder: verschiedene Hände, Münzen, Lichtverhältnisse und Hintergründe.

Ein Spezialmodell ist enger. Es kann zum Beispiel auf eine bestimmte Münze, eine bestimmte Bühne oder einen bestimmten Performer abgestimmt sein.

Für Deine Dienstleistung ist das spannend: Zauberer können Rohbilder einreichen, und daraus kann ein passendes Modell entstehen.

## Gute Rohbilder

Sammle Bilder, die zur echten Nutzung passen.

- Münze in einer Hand.
- Münze auf Filz oder einfarbigem Untergrund.
- Verschiedene Münzen und Pokermünzen.
- Helle und dunkle Münzen.
- Verschiedene Lichtverhältnisse.
- Schatten und leichte Schräglage.
- Sharpie-Initialen oder Markierungen.

Schwierige Bilder sind okay, solange man die Münze noch sinnvoll markieren kann.

## Schlechte Rohbilder

Diese Bilder helfen meistens wenig:

- stark unscharf.
- Münze abgeschnitten.
- Münze fast vollständig verdeckt.
- mehrere Münzen dicht nebeneinander.
- Bild so dunkel oder reflektierend, dass der Rand nicht mehr erkennbar ist.

Wenn Du beim Markieren selbst raten muesstest, ist das Bild wahrscheinlich kein gutes Trainingsbild.

## Was passiert nach dem Markieren?

Der Desktop-Trainer erzeugt ein annotiertes Dataset:

```text
mcs-annotated-dataset-v1.zip
  images/
  masks/
  metadata.json
```

Danach läuft der Trainingsprozess. Daraus entsteht ein ONNX-Modell und optional ein Modellpaket:

```text
coin-segmentation.onnx
mcs-model-<profile>-<version>.zip
```

Beim Übernehmen in die PWA installiert der Trainer das Modell unter `wwwroot/models/<model-id>/` und aktualisiert `wwwroot/models/manifest.json` (`schemaVersion = mcs-model-index-v1`). Wenn ein vorhandenes Modell ersetzt wird, erstellt die GUI nach Bestätigung ein Backup.

In MagicCoinSnapper wählst Du das Scan-Modell unter **Einstellungen**. Ohne Manifest nutzt die App weiterhin den alten Pfad `wwwroot/models/coin-segmentation.onnx`, falls diese Datei vorhanden ist.

## Datenschutz

Die PWA sammelt Bilder lokal im Browser.

Erst wenn Du ein ZIP exportierst und weitergibst, verlassen die Bilder Dein Gerät. Der Versand passiert bewusst und manuell mit Werkzeugen Deiner Wahl.

## Kurz gesagt

Du sammelst auf dem Smartphone echte Beispielbilder. Auf dem Desktop werden sie sauber markiert, trainiert und als Modell in die PWA übernommen. Die Vorführapp bleibt schlank, schnell und offlinefähig.
