# Trainer-GUI

Die PySide6-GUI fuehrt den Trainer-Workflow von der Raw-ZIP bis zum PWA-Modell.

Fuer praxisorientierte Hinweise zu Bildmengen, Aufnahmequalitaet, Maskierung, mehreren Helfer-ZIPs und Modellfeldern siehe `trainer/docs/training-faq.md`.

## Start

```pwsh
cd trainer
python -m pip install -e .[ml,gui]
mcs-trainer gui
```

Optional kann ein Dataset direkt geoeffnet werden:

```pwsh
mcs-trainer gui --dataset .\data\annotated\coins-v1
```

## Workflow

1. Raw-ZIP importieren.
2. Muenze pro Bild als Maske markieren.
3. Daten speichern.
4. **Daten pruefen** ausfuehren.
5. **Daten aufteilen** fuer Train/Val/Test.
6. **Training starten** und Konfiguration setzen.
7. **Modell testen**.
8. **ONNX exportieren**.
9. **Modellpaket erstellen**.
10. **Modell in PWA uebernehmen**.

Training, Test und Export laufen als Hintergrundprozesse mit Log-Anzeige. Die Masken werden als PNG im Modus `L` mit Werten `0` und `255` gespeichert.

## PWA-Uebernahme

Beim Uebernehmen installiert die GUI das Modell unter `wwwroot/models/<model-id>/` und aktualisiert `wwwroot/models/manifest.json`. Vor dem Ersetzen vorhandener Dateien fragt die GUI nach und erstellt Backups.
