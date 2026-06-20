# Modellverwaltung

MagicCoinSnapper unterstuetzt mehrere Scan-Modelle. Die PWA liest sie aus `wwwroot/models/manifest.json` und bietet sie in den Einstellungen als Scan-Modell an.

## Layout

```text
wwwroot/models/
  manifest.json
  <model-id>/
    coin-segmentation.onnx
    model.json
    metrics.json
    preprocessing.json
```

## Manifest

```json
{
  "schemaVersion": "mcs-model-index-v1",
  "models": [
    {
      "id": "general-001",
      "displayName": "General 001",
      "version": "1.0.0",
      "path": "models/general-001/coin-segmentation.onnx",
      "output": { "threshold": 0.5 }
    }
  ]
}
```

`path` ist relativ zu `wwwroot`. `output.threshold` ist optional und faellt auf `0.5` zurueck.

## Installation Durch Die GUI

Die Aktion **Modell in PWA uebernehmen** kopiert das Modell nach `wwwroot/models/<model-id>/` und aktualisiert den Manifest-Eintrag. Wenn ein Modell oder Manifest ersetzt wird, erstellt die GUI nach Bestaetigung ein Backup.

## Fallback

Wenn kein Manifest verfuegbar ist, versucht die PWA weiter `wwwroot/models/coin-segmentation.onnx` zu laden. Wenn auch diese Datei fehlt, nutzt sie die lokale Kreis-/Kontur-Heuristik.
