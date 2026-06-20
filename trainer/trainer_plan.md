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

## Status

Alle MVP-Phasen (1-10) sind umgesetzt und verifiziert. End-to-end-Smoke (validate -> split -> train -> evaluate -> export-onnx -> package-model) laeuft durch, 28 Tests sind gruen.

- Phase 1: `trainer/` Python-Projekt mit `pyproject.toml`, Paket `mcs_trainer`, editable installiert.
- Phase 2: CLI-Grundlage mit Raw-ZIP-Import (`import-raw`).
- Phase 3: Dataset-Schema per Pydantic v2 und Validierung (`validate`, raw + annotated).
- Phase 4: PySide6-Bildviewer (`image_viewer.py`).
- Phase 5: Maskenwerkzeuge Pinsel/Radierer/Ellipse/Undo/Redo (`mask_editor.py`).
- Phase 6: Metadatenpanel und Dataset-Speicherung (`metadata_panel.py`, `annotated_dataset.py`).
- Phase 7: Trainingspipeline mit PyTorch (`train`, `evaluate`, U-Net, BCE+Adam, Checkpoints).
- Phase 8: ONNX-Export und ONNX-Validierung (`export-onnx`, feste Shapes, onnxsim).
- Phase 9: Modellpaket-Erzeugung (`package-model`, zip mit Metadaten und SHA256SUMS).
- Phase 10: PWA-Smoke-Test, ONNX nach `wwwroot/models/coin-segmentation.onnx` kopiert (aktuell Smoke-Modell, noch kein Produktionsmodell).
