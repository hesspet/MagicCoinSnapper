# How To Train Your App

Diese Anleitung erklaert den neuen Trainingsablauf fuer MagicCoinSnapper.

Kurz gesagt: Das Smartphone sammelt Bilder. Der Desktop macht die genaue Markierung. Das Modell entsteht danach lokal im Trainingsworkflow.

## Warum der Ablauf getrennt ist

Auf dem Smartphone ist die App fuer die Vorfuehrung gedacht: schnell, dunkel, einhaendig bedienbar und offline.

Masken sauber zu zeichnen ist dort aber unpraktisch. Mit Maus, grossem Bildschirm und Tastatur geht das deutlich besser. Darum wird die Arbeit getrennt:

- Smartphone: Rohbilder sammeln.
- Desktop-Trainer: Bilder sichten, Muenze markieren, Metadaten pflegen.
- Trainingspipeline: Modell trainieren und als ONNX exportieren.
- PWA: fertiges Modell automatisch fuer den Scan nutzen.

## Was bedeutet Training jetzt?

Training bedeutet nicht, dass die PWA selbst auf dem Smartphone rechnet und lernt.

Die PWA liefert nur gute Beispielbilder. Auf dem Desktop entstehen daraus saubere Trainingsdaten: Bild plus Maske plus Metadaten.

Aus diesen Trainingsdaten wird ein Modell gebaut. Dieses Modell wird spaeter in die App gelegt oder als Modellpaket bereitgestellt.

## Was ist eine Maske?

Eine Maske markiert die Muenze im Bild.

Alles innerhalb der Maske gehoert zur Muenze. Alles ausserhalb wird beim spaeteren Scan transparent.

Diese Maske zeichnest Du nicht mehr auf dem Smartphone, sondern im Desktop-Trainer.

## Schritt 1: Expertenmodus aktivieren

1. Oeffne MagicCoinSnapper.
2. Gehe zu **Einstellungen**.
3. Aktiviere **Bildersammlung anzeigen**.
4. Im Menue erscheint **Bildersammlung**.

Der Schalter ist lokal. Er gilt nur auf diesem Geraet und nur in diesem Browser.

## Schritt 2: Rohbilder sammeln

1. Gehe zu **Scan**.
2. Nimm ein Bild auf oder lade ein Bild aus der Galerie.
3. Oeffne **Bildersammlung**.
4. Tippe auf **Aktuelles Scanbild verwenden**.
5. Fuege optional eine kurze Notiz hinzu.
6. Tippe auf **Rohbild speichern**.
7. Wiederhole das mit mehreren Bildern.

Du kannst in der Bildersammlung auch direkt ein Bild aus der Galerie laden.

## Schritt 3: Raw-ZIP exportieren

1. Oeffne **Bildersammlung**.
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

Die `metadata.json` beschreibt die Bilder und enthaelt Notizen, Quelle, Groesse und Zeitpunkt.

## Schritt 4: Auf dem Desktop markieren

Der Desktop-Trainer importiert das Raw-ZIP.

Dort kannst Du:

- Bilder durchblaettern.
- Reinzoomen.
- Die Muenze mit Maus oder Stift markieren.
- Fehler schnell korrigieren.
- Bilder ausschliessen.
- Metadaten pflegen.
- Trainingsgruppen setzen.

Das ist der richtige Ort fuer genaue Maskenarbeit.

## Welche Metadaten sind sinnvoll?

Metadaten helfen spaeter, verschiedene Modelle zu trainieren.

Beispiele:

- Muenze in Hand.
- Filzuntergrund.
- Pokermuenze.
- Silberdollar.
- Buehnenlicht.
- Sharpie-Markierung sichtbar.
- Schwieriger Fall.
- Fuer allgemeines Modell geeignet.
- Fuer Spezialmodell geeignet.

Damit kannst Du spaeter gezielt trainieren: allgemein, nur Pokermuenzen, nur eine bestimmte Muenze oder nur eine bestimmte Show-Situation.

## Allgemeines Modell oder Spezialmodell?

Ein allgemeines Modell soll fuer viele Anwender funktionieren. Dafuer braucht es viele unterschiedliche Bilder: verschiedene Haende, Muenzen, Lichtverhaeltnisse und Hintergruende.

Ein Spezialmodell ist enger. Es kann zum Beispiel auf eine bestimmte Muenze, eine bestimmte Buehne oder einen bestimmten Performer abgestimmt sein.

Fuer Deine Dienstleistung ist das spannend: Zauberer koennen Rohbilder einreichen, und daraus kann ein passendes Modell entstehen.

## Gute Rohbilder

Sammle Bilder, die zur echten Nutzung passen.

- Muenze in einer Hand.
- Muenze auf Filz oder einfarbigem Untergrund.
- Verschiedene Muenzen und Pokermuenzen.
- Helle und dunkle Muenzen.
- Verschiedene Lichtverhaeltnisse.
- Schatten und leichte Schraeglage.
- Sharpie-Initialen oder Markierungen.

Schwierige Bilder sind okay, solange man die Muenze noch sinnvoll markieren kann.

## Schlechte Rohbilder

Diese Bilder helfen meistens wenig:

- stark unscharf.
- Muenze abgeschnitten.
- Muenze fast vollstaendig verdeckt.
- mehrere Muenzen dicht nebeneinander.
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

Danach laeuft der Trainingsprozess. Daraus entsteht ein ONNX-Modell:

```text
coin-segmentation.onnx
```

Dieses Modell kann die PWA fuer den automatischen Scan verwenden.

## Datenschutz

Die PWA sammelt Bilder lokal im Browser.

Erst wenn Du ein ZIP exportierst und weitergibst, verlassen die Bilder Dein Geraet. Der Versand passiert bewusst und manuell mit Werkzeugen Deiner Wahl.

## Kurz gesagt

Du sammelst auf dem Smartphone echte Beispielbilder. Auf dem Desktop werden sie sauber markiert. Daraus entsteht ein besseres Modell. Die Vorfuehrapp bleibt schlank, schnell und offlinefaehig.
