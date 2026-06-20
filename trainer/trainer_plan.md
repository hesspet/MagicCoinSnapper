# Trainer-Plan

Der Trainer ist die lokale Desktop-/CLI-Komponente fuer MagicCoinSnapper.

## Zweck

Die Smartphone-PWA sammelt Rohbilder und exportiert `mcs-raw-images-v1.zip`.

Der Trainer importiert diese ZIP-Dateien, ermoeglicht genaue Maskenannotation am Desktop und erstellt daraus Trainingsdaten und ONNX-Modelle.

## Festgelegte Technik

- Python 3.12
- PySide6 fuer die Desktop-App
- Typer + Rich fuer CLI
- PyTorch fuer Training
- OpenCV/Pillow/NumPy fuer Bildverarbeitung
- Albumentations fuer Augmentierungen
- ONNX, ONNX Runtime und ONNX Simplifier fuer Export/Validierung
- GPU darf genutzt werden; CPU-Fallback bleibt sinnvoll
- Online-Komponenten sind im Trainingsworkflow erlaubt

## MVP-Reihenfolge

1. CLI-Projektstruktur erstellen.
2. Raw-ZIP aus PWA importieren.
3. Dataset-Schema versionieren.
4. Validierung fuer Raw- und Annotated-Datasets bauen.
5. PySide6-Bildviewer bauen.
6. Maskenzeichnen mit Pinsel, Radierer, Ellipse, Undo/Redo bauen.
7. Metadaten pro Bild pflegen.
8. Annotated Dataset exportieren.
9. PyTorch Training anbinden.
10. ONNX exportieren und gegen PWA-Vertrag pruefen.

## CLI-Zielcommands

```pwsh
mcs-trainer import-raw --zip .\data\incoming\mcs-raw-images.zip
mcs-trainer validate --dataset .\data\annotated\coins-v1
mcs-trainer split --dataset .\data\annotated\coins-v1
mcs-trainer train --dataset .\data\annotated\coins-v1 --profile general --device cuda
mcs-trainer evaluate --run .\runs\coinseg\general-001
mcs-trainer export-onnx --run .\runs\coinseg\general-001
mcs-trainer package-model --onnx .\exports\coin-segmentation.onnx
```

## PWA-Kompatibilitaet

Die PWA erwartet vorerst:

```text
wwwroot/models/coin-segmentation.onnx
```

ONNX-Vertrag:

```text
input:  float32[1,3,512,512], RGB, 0..1
output: float32[1,1,512,512], probability mask, 0..1
threshold: 0.5
```

## Wichtig Fuer Die Naechste Session

Nicht zuerst die komplette GUI bauen. Besser zuerst einen stabilen CLI-Kern erstellen:

- `pyproject.toml`
- `src/mcs_trainer/cli/main.py`
- `src/mcs_trainer/dataset/schemas.py`
- `src/mcs_trainer/dataset/raw_zip.py`
- `import-raw` Command
- `validate` Command

Erst wenn Import und Schema sauber sind, die PySide6-App darauf aufbauen.
