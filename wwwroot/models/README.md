# Modelle

MagicCoinSnapper kann mehrere gebuendelte ONNX-Modelle ueber eine Manifestdatei anbieten:

```json
{
  "schemaVersion": "mcs-model-index-v1",
  "models": [
    {
      "id": "general-001",
      "displayName": "General 001",
      "description": "Standardmodell fuer Scan-Ergebnisse.",
      "version": "1.0.0",
      "path": "models/general-001/coin-segmentation.onnx",
      "output": { "threshold": 0.5 }
    }
  ]
}
```

Speichere das Manifest als `wwwroot/models/manifest.json`. Modelle liegen unter `wwwroot/models/<model-id>/`. `path` zeigt auf eine Datei unter `wwwroot`, `output.threshold` ist optional und faellt auf `0.5` zurueck.

Der Trainer kann Modelle ueber die GUI in die PWA uebernehmen. Dabei werden vorhandene Modellverzeichnisse oder Manifeste nur nach Bestaetigung ersetzt und vorher gesichert.

In den PWA-Einstellungen kann das Scan-Modell aus dem Manifest gewaehlt werden. Ohne Manifest bleibt der Legacy-Pfad aktiv, falls `wwwroot/models/coin-segmentation.onnx` existiert. Fehlt auch diese Datei, verwendet MagicCoinSnapper die lokale Kreis-/Kontur-Heuristik fuer Scan-Ergebnisse.
