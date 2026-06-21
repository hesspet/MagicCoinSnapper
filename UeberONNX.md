# Über ONNX und die Münzerkennung

MagicCoinSnapper soll eine Münze direkt auf dem Gerät erkennen, freistellen und als PNG mit transparentem Hintergrund speichern. Dafür wird ONNX verwendet.

## Was ist ONNX?

ONNX ist ein Format für Erkennungsmodelle. Ein solches Modell kann lernen, welche Bildbereiche zu einer Münze gehören und welche nicht.

Für Anwender bedeutet das: Die App kann später ein Foto auswerten, ohne dass das Bild an einen Server geschickt werden muss.

## Warum nutzt MagicCoinSnapper ONNX?

MagicCoinSnapper ist für den Einsatz auf der Bühne gedacht. Dort muss der Ablauf schnell, zuverlässig und möglichst unabhängig vom Internet sein.

ONNX hilft dabei, die Erkennung lokal im Browser laufen zu lassen. Das ist wichtig für Datenschutz, Offline-Nutzung und kurze Wege während einer Show.

## Was passiert beim Scannen?

Beim Scan nimmt die App ein Bild aus der Kamera oder Galerie. Danach sucht das Modell die Münze im Bild.

Das Ziel ist ein eng zugeschnittenes Münzbild. Der Bereich um die Münze wird transparent, damit das Ergebnis als PNG weiterverwendet werden kann.

## Wo entstehen Trainingsdaten?

Die PWA sammelt nur Rohbilder. Das ist auf dem Smartphone schnell und passt zum Show-Ablauf.

Die genaue Markierung der Münze passiert später im Desktop-Trainer. Dort ist das Zeichnen mit Maus, Stift und großem Bildschirm deutlich einfacher.

## Warum braucht die App Training?

Münzen sehen sehr unterschiedlich aus. Sie können hell, dunkel, spiegelnd, beschriftet oder schräg zur Kamera liegen. Auch Hände, Schatten und Untergründe verändern das Bild.

Training hilft dem Modell, diese Unterschiede zu lernen. Je besser die gesammelten Rohbilder und die späteren Desktop-Markierungen sind, desto besser wird später der automatische Scan.

## So entstehen gute Trainingsbilder

- Die Münze ist vollständig sichtbar.
- Die Hand haelt ruhig.
- Die Münze ist nicht zu klein im Bild.
- Der Rand der Münze ist möglichst erkennbar.
- Es gibt Beispiele mit verschiedenen Händen, Münzen und Lichtverhältnissen.
- Auch schwierige Fälle sind sinnvoll: Schatten, leichte Schräglage, Filzuntergrund, Pokermünzen und Sharpie-Markierungen.

## Schlechte Trainingsbilder

- Die Münze ist stark verdeckt.
- Das Bild ist unscharf.
- Die Münze ist nur angeschnitten.
- Der Rand ist durch starke Spiegelung kaum sichtbar.
- Mehrere Münzen liegen dicht beieinander, obwohl nur eine erkannt werden soll.

## Bildersammlung im Expertenmodus

Die Bildersammlung ist ein Expertenmodus. Dort können Rohbilder lokal gespeichert und als ZIP exportiert werden.

Das ZIP kann manuell weitergegeben werden, zum Beispiel per E-Mail, Upload oder Messenger. Die App sendet nichts automatisch.

## Offline-Nutzung

Ziel ist, dass App und Modell offline funktionieren. Rohbilder bleiben lokal im Browser gespeichert und können als ZIP exportiert werden.

Bei einem App-Update kann ein neues Modell ausgeliefert werden. Nach dem Laden soll es wieder offline bereitstehen.

## Datenschutz

Bilder bleiben auf dem Gerät, solange sie nicht bewusst exportiert werden.

Der Export ist fuer den Desktop-Trainer gedacht. Nur exportierte Dateien verlassen den Browser.

## Kurz gesagt

ONNX ist die Grundlage für die automatische Münzerkennung. Die PWA sammelt Rohbilder, der Desktop-Trainer erstellt daraus saubere Trainingsdaten. Der spätere Scan soll ohne Korrektur eine freigestellte Münze als transparentes PNG erzeugen.
