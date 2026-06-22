# Modellverwaltung

MagicCoinSnapper unterstuetzt mehrere Scan-Modelle. Die PWA liest sie aus `wwwroot/models/manifest.json` und bietet sie in den Einstellungen als Scan-Modell an.

Eine anwenderorientierte Erklaerung zu Modell-ID, Naming, Versionen und Loeschen von Modellen steht in `trainer/docs/training-faq.md`.

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
      "contract": "mcs-segmentation-512-letterbox-v1",
      "modelUrl": "models/general-001/coin-segmentation.onnx",
      "output": { "threshold": 0.5 }
    }
  ]
}
```

`modelUrl` ist relativ zu `wwwroot`. Aeltere Eintraege mit `path` werden ebenfalls gelesen. `output.threshold` ist optional und faellt in der PWA auf `0.5` zurueck.

## Installation Durch Die GUI

Die Aktion **Modell in PWA uebernehmen** kopiert das Modell nach `wwwroot/models/<model-id>/` und aktualisiert den Manifest-Eintrag. Wenn ein Modell oder Manifest ersetzt wird, erstellt die GUI nach Bestaetigung ein Backup.

## Kein Modell / Fallback

Wenn kein gueltiges Manifest mit nutzbaren Modelleintraegen verfuegbar ist, bietet die PWA kein trainiertes Scan-Modell zur Auswahl an und nutzt die lokale Kreis-/Kontur-Heuristik.

Zum Entfernen eines Modells muessen sowohl das Verzeichnis `wwwroot/models/<model-id>/` als auch der passende Eintrag in `wwwroot/models/manifest.json` entfernt werden. Zeigt `defaultModelId` auf das entfernte Modell, muss der Wert auf ein anderes Modell oder `null` gesetzt werden.
