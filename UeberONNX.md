# Ueber ONNX und die Muenzerkennung

MagicCoinSnapper soll eine Muenze direkt auf dem Geraet erkennen, freistellen und als PNG mit transparentem Hintergrund speichern. Dafuer wird ONNX verwendet.

## Was ist ONNX?

ONNX ist ein Format fuer Erkennungsmodelle. Ein solches Modell kann lernen, welche Bildbereiche zu einer Muenze gehoeren und welche nicht.

Fuer Anwender bedeutet das: Die App kann spaeter ein Foto auswerten, ohne dass das Bild an einen Server geschickt werden muss.

## Warum nutzt MagicCoinSnapper ONNX?

MagicCoinSnapper ist fuer den Einsatz auf der Buehne gedacht. Dort muss der Ablauf schnell, zuverlaessig und moeglichst unabhaengig vom Internet sein.

ONNX hilft dabei, die Erkennung lokal im Browser laufen zu lassen. Das ist wichtig fuer Datenschutz, Offline-Nutzung und kurze Wege waehrend einer Show.

## Was passiert beim Scannen?

Beim Scan nimmt die App ein Bild aus der Kamera oder Galerie. Danach sucht das Modell die Muenze im Bild.

Das Ziel ist ein eng zugeschnittenes Muenzbild. Der Bereich um die Muenze wird transparent, damit das Ergebnis als PNG weiterverwendet werden kann.

## Wo entstehen Trainingsdaten?

Die PWA sammelt nur Rohbilder. Das ist auf dem Smartphone schnell und passt zum Show-Ablauf.

Die genaue Markierung der Muenze passiert spaeter im Desktop-Trainer. Dort ist das Zeichnen mit Maus, Stift und grossem Bildschirm deutlich einfacher.

## Warum braucht die App Training?

Muenzen sehen sehr unterschiedlich aus. Sie koennen hell, dunkel, spiegelnd, beschriftet oder schraeg zur Kamera liegen. Auch Haende, Schatten und Untergruende veraendern das Bild.

Training hilft dem Modell, diese Unterschiede zu lernen. Je besser die gesammelten Rohbilder und die spaeteren Desktop-Markierungen sind, desto besser wird spaeter der automatische Scan.

## So entstehen gute Trainingsbilder

- Die Muenze ist vollstaendig sichtbar.
- Die Hand haelt ruhig.
- Die Muenze ist nicht zu klein im Bild.
- Der Rand der Muenze ist moeglichst erkennbar.
- Es gibt Beispiele mit verschiedenen Haenden, Muenzen und Lichtverhaeltnissen.
- Auch schwierige Faelle sind sinnvoll: Schatten, leichte Schraeglage, Filzuntergrund, Pokermuenzen und Sharpie-Markierungen.

## Schlechte Trainingsbilder

- Die Muenze ist stark verdeckt.
- Das Bild ist unscharf.
- Die Muenze ist nur angeschnitten.
- Der Rand ist durch starke Spiegelung kaum sichtbar.
- Mehrere Muenzen liegen dicht beieinander, obwohl nur eine erkannt werden soll.

## Bildersammlung im Expertenmodus

Die Bildersammlung ist ein Expertenmodus. Dort koennen Rohbilder lokal gespeichert und als ZIP exportiert werden.

Das ZIP kann manuell weitergegeben werden, zum Beispiel per E-Mail, Upload oder Messenger. Die App sendet nichts automatisch.

## Offline-Nutzung

Ziel ist, dass App und Modell offline funktionieren. Rohbilder bleiben lokal im Browser gespeichert und koennen als ZIP exportiert werden.

Bei einem App-Update kann ein neues Modell ausgeliefert werden. Nach dem Laden soll es wieder offline bereitstehen.

## Datenschutz

Bilder bleiben auf dem Geraet, solange sie nicht bewusst exportiert werden.

Der Export ist fuer den Desktop-Trainer gedacht. Nur exportierte Dateien verlassen den Browser.

## Kurz gesagt

ONNX ist die Grundlage fuer die automatische Muenzerkennung. Die PWA sammelt Rohbilder, der Desktop-Trainer erstellt daraus saubere Trainingsdaten. Der spaetere Scan soll ohne Korrektur eine freigestellte Muenze als transparentes PNG erzeugen.
