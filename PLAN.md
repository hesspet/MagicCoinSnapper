# MagicCoinSnapper – Verbesserungsplan

> Stand: 2026-06-21

## Übersicht

Dieser Plan beschreibt die schrittweise Verbesserung der Bilderkennung,
des Scanner-Workflows und der Trainingspipeline. Jeder Task ist so
bemessen, dass er in einer Session bearbeitet werden kann.

Die Tasks sind nach Phasen geordnet. Phase 1 enthält die Änderungen mit
dem größten Impact auf die Segmentierungsqualität.

---

## Phase 1: Segmentierungsqualität (High Impact)

### 1.1 Letterbox-Resize statt Direct Stretch

**Problem:** `coin-processing.js:82` und `augmentations.py:9` stretchen
Bilder direkt auf 512×512. Bei nicht-quadratischen Fotos (4:3, 16:9)
wird die Münze elliptisch verzerrt.

**Lösung:** Aspect-Ratio erhalten, auf 512×512 auffüllen (Letterbox).

**Dateien:**
- `trainer/src/mcs_trainer/ml/augmentations.py` – `A.Resize(512,512)` → `A.LongestMaxSize(512)` + `A.PadIfNeeded(512,512)`
- `trainer/src/mcs_trainer/ml/dataset.py` – muss die Letterbox-Padding-Info maskieren (nur Bildbereich, nicht Padding)
- `wwwroot/js/coin-processing.js:77-90` – Letterbox-Resize + Padding im PWA-Inference-Pfad
- `wwwroot/models/manifest.json` – Input Contract ändern (Hinweis: Padding statt Stretch)

**Abhängigkeiten:** Retraining aller Modelle erforderlich (Contract-Änderung).

### 1.2 DiceLoss (oder BCE+Dice Hybrid)

**Problem:** `train_loop.py:114` verwendet `BCELoss`. BCE optimiert
Pixel-genau, nicht Boundary-genau. Bei Klassenungleichgewicht (Hintergrund)
suboptimal.

**Lösung:** DiceLoss oder BCE+Dice-Hybrid als Loss-Funktion.

**Dateien:**
- `trainer/src/mcs_trainer/ml/metrics.py` – `dice_loss()` Funktion ergänzen
- `trainer/src/mcs_trainer/ml/train_loop.py:114` – Loss durch Hybrid ersetzen

**Abhängigkeiten:** Retraining erforderlich.

### 1.3 Reiche Augmentation

**Problem:** `augmentations.py` hat nur 5 schwache Augmentierungen.
Bei nur 46 Trainingsbildern massives Overfitting.

**Lösung:** Augmentations-Pipeline erweitern.

**Dateien:**
- `trainer/src/mcs_trainer/ml/augmentations.py`
  - `A.RandomScale`, `A.Perspective`, `A.GaussianBlur`, `A.GaussNoise`
  - `A.ColorJitter`, `A.RandomGamma`, `A.HueSaturationValue`
  - `A.CoarseDropout` (simuliert Markierungen/Reflexionen)
  - `A.Rotate` auf `limit=180` erhöhen
  - `A.RandomBrightnessContrast` auf `p=0.8` erhöhen, limits verdoppeln

**Abhängigkeiten:** Keine (Augmentation nur im Training).

### 1.4 Rohe Maske als Output (Ellipse nur Fallback)

**Problem:** `coin-processing.js:441-458` zwingt jede Maske in eine
Ellipse mit Aspect-Ratio-Clamping. Die Segmentierungsleistung des U-Net
wird weggeworfen.

**Lösung:** Die rohe binäre Maske als Output verwenden. Die Ellipse
nur als Fallback, wenn die Maske leer oder zu fragmentiert ist.

**Dateien:**
- `wwwroot/js/coin-processing.js:410-438` (`createCutout`) – Maske direkt
  als Alphakanal nutzen statt Ellipse
- `coin-processing.js:441-458` (`createFinalEllipseGeometry`) – in
  Fallback-Funktion umwandeln

**Abhängigkeiten:** Keine (reiner JS-Code, kein Retraining).

### 1.5 Connected Components verbessern

**Problem:** `analyzeMask()` (`coin-processing.js:329-378`) nimmt nur
die größte Komponente. Bei Löchern/Reflexionen zerbricht die Maske.

**Lösung:** Morphologische Dilation vor Component-Analyse. Optional
alle signifikanten Komponenten zusammenführen.

**Dateien:**
- `wwwroot/js/coin-processing.js:329-408` – Dilation-Step ergänzen
  (kleine Canvas-Operation mit 3×3 oder 5×5 Kernel)

**Abhängigkeiten:** 1.4 (rohe Maske) – weil die Ellipse aktuell das
Zerbrechen der Maske kaschiert.

---

## Phase 2: Training Pipeline (Medium Impact)

### 2.1 Learning Rate Scheduling

**Problem:** `train_loop.py:115` – feste LR 1e-3 ohne Scheduler.

**Lösung:** Cosine Annealing oder ReduceLROnPlateau.

**Dateien:**
- `trainer/src/mcs_trainer/ml/train_loop.py` – Scheduler ergänzen,
  in `TrainConfig` aufnehmen

**Abhängigkeiten:** Retraining empfohlen.

### 2.2 Datensatz erweitern

**Problem:** Nur 46 annotierte Bilder. Zu wenig für ein robustes Modell.

**Lösung:** Ziel 300-500 Bilder. Systematisch verschiedene Szenarien:
- Unterschiedliche Hände, Untergründe (Filz, Tisch, Handfläche)
- Verschiedene Münzen (Größe, Farbe, Material)
- Unterschiedliche Lichtverhältnisse
- Schräge Perspektiven

**Dateien:**
- `trainer/trainer/data/annotated/` – neue Bilder + Masken
- `trainer/trainer/data/raw/` – neue Rohbilder

**Abhängigkeiten:** Manuelle Arbeit (fotografieren + annotieren).

### 2.3 k-Fold Cross-Validation

**Problem:** Ein Train/Val/Test-Split bei 46 Bildern ist nicht robust.

**Lösung:** 5-Fold Cross-Validation im Training, Mittelwert der Metriken.

**Dateien:**
- `trainer/src/mcs_trainer/ml/train_loop.py` – k-Fold-Logik ergänzen
- `trainer/src/mcs_trainer/dataset/splits.py` – k-Fold-Generierung

**Abhängigkeiten:** 2.2 (größeres Dataset macht k-Fold sinnvoller).

### 2.4 FP16-Quantisierung für ONNX

**Problem:** ONNX-Modelle sind ~7,6 MB. WASM-Inference single-threaded.

**Lösung:** FP16-Quantisierung (`onnxconverter-common` oder
`onnxruntime.transformers.optimizer`). Reduziert Größe um ~50%,
beschleunigt Inference.

**Dateien:**
- `trainer/src/mcs_trainer/ml/onnx_export.py` – Quantisierungs-Step
  nach dem Export
- `wwwroot/js/coin-processing.js` – ggf. Session-Options anpassen

**Abhängigkeiten:** Keine (optionaler Optimierungsschritt).

---

## Phase 3: Scanner/Camera UX (Medium Impact)

### 3.1 Circle-Overlay auf Kamera

**Problem:** Keine visuelle Hilfestellung beim Positionieren der Münze.

**Lösung:** SVG/Canvas-Overlay auf dem `<video>`-Element, das eine
Kreis-Markierung anzeigt.

**Dateien:**
- `Pages/Camera.razor` – Overlay-Element ergänzen
- `Pages/Camera.razor.css` – Overlay-Styling
- `Pages/Camera.razor.js` – Overlay bei Kamerastart anzeigen

**Abhängigkeiten:** Keine.

### 3.2 Live-Segmentierungs-Vorschau

**Problem:** User sieht erst nach dem Scan, ob die Position passt.

**Lösung:** ONNX-Inference in regelmäßigen Abständen (alle 500ms) auf
dem Kamera-Stream, Ergebnis als Overlay anzeigen.

**Dateien:**
- `Pages/Camera.razor.js` – Timer-gesteuerte Inference
- `wwwroot/js/coin-processing.js` – ggf. optimierte Lightweight-Version
- `Pages/Camera.razor` – Overlay für Maske

**Abhängigkeiten:** 1.4 (rohe Maske), da die Ellipse kein gutes
Live-Feedback gibt.

### 3.3 Auto-Capture

**Problem:** User muss manuell Auslösen, verwackelt oft.

**Lösung:** Bewegungserkennung + Münzgrößen-Prüfung → automatisch
Auslösen wenn Münze stabil im Bild ist.

**Dateien:**
- `Pages/Camera.razor.js` – Frame-Differenz + Größencheck vor Auto-Capture
- `Pages/Camera.razor` – Auto-Capture-Toggle

**Abhängigkeiten:** 3.2 (teilt sich die Frame-Analyse-Logik).

### 3.4 Burst + Sharpness-Selection

**Problem:** Einzelbild oft verwackelt oder unscharf.

**Lösung:** 3-5 Frames schnell aufnehmen, schärfsten behalten
(Laplace-Varianz als Metrik).

**Dateien:**
- `Pages/Camera.razor.js` – Burst-Capture + Sharpness-Metrik
- `wwwroot/js/coin-processing.js` – `sharpness()`-Helfer

**Abhängigkeiten:** Keine.

---

## Phase 4: Infrastruktur & Code-Qualität (Low Impact)

### 4.1 Unit Tests für coin-processing.js

**Problem:** Keine Tests für Mask-Analyse, Ellipsen-Geometrie,
Heuristik-Fallback.

**Lösung:** Vitest/Jest-Tests für die Kernfunktionen.

**Dateien:**
- `tests/js/coin-processing.test.js` (neu)
- `package.json` – vitest-dev-Dependency ergänzen

**Abhängigkeiten:** Keine.

### 4.2 Magic Numbers in Konstanten

**Problem:** 512, 0.5, 0.08, 1.38 etc. sind hartcodiert und
undokumentiert.

**Lösung:** Constants-Modul oder Objekt mit dokumentierten Konstanten.

**Dateien:**
- `wwwroot/js/coin-processing.js` – Konstanten extrahieren
- `wwwroot/js/constants.js` (neu) oder Config-Objekt in coin-processing

**Abhängigkeiten:** Keine.

### 4.3 Active Learning

**Problem:** Alle Bilder werden gleich behandelt. Keine Priorisierung.

**Lösung:** Nach jedem Training: Unsicherheit pro Bild messen
(Entropie der Prediction). Unsichere Bilder für Annotation vorschlagen.

**Dateien:**
- `trainer/src/mcs_trainer/cli/main.py` – `active-learn`-Kommando
- `trainer/src/mcs_trainer/ml/` – Uncertainty-Sampling-Logik

**Abhängigkeiten:** 2.2 (größeres Dataset nötig für sinnvolles Active Learning).

---

## Abhängigkeitsgraph

```
1.1 Letterbox     ───→ Retraining ALLER Modelle
1.2 DiceLoss      ───→ Retraining
1.3 Augmentation  ───→ (keine)
1.4 Rohe Maske    ───→ (keine)
1.5 Components    ───→ erst nach 1.4 sinnvoll
    │
2.1 LR Scheduler  ───→ Retraining empfohlen
2.2 Dataset       ───→ manuelle Arbeit
2.3 k-Fold        ───→ erst nach 2.2 sinnvoll
2.4 FP16          ───→ (keine)
    │
3.1 Circle-Overlay──→ (keine)
3.2 Live-Vorschau  ───→ erst nach 1.4 sinnvoll
3.3 Auto-Capture   ───→ erst nach 3.2 sinnvoll
3.4 Burst          ───→ (keine)
    │
4.1 Tests         ───→ (keine)
4.2 Konstanten    ───→ (keine)
4.3 Active Learning──→ erst nach 2.2 sinnvoll
```

## Empfohlene Reihenfolge

| Session | Tasks | Begründung |
|---|---|---|
| 1 | 1.4 (rohe Maske) + 1.3 (Augmentation) | High Impact, kein Retraining nötig (1.4) |
| 2 | 1.2 (DiceLoss) + 2.1 (LR Scheduler) | Loss + Scheduler im Training |
| 3 | 1.1 (Letterbox) | Contract-Änderung, neues Modell trainieren |
| 4 | 1.5 (Components) + 3.1 (Overlay) | Post-Processing + UX |
| 5 | 2.2 (Dataset erweitern) + 2.3 (k-Fold) | Datenqualität |
| 6 | 3.2 (Live-Vorschau) + 3.3 (Auto-Capture) | Kamera-UX |
| 7 | 2.4 (FP16) + 4.1 (Tests) + 4.2 (Konstanten) | Optimierung & Qualität |
| 8 | 4.3 (Active Learning) | Advanced |
