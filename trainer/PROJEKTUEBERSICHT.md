# Projektuebersicht - MagicCoinSnapper Trainer

## Kurzprofil

Der MagicCoinSnapper Trainer ist eine lokale Desktop-/CLI-Anwendung fuer Windows. Er verarbeitet Rohbilder aus der MagicCoinSnapper PWA, ermoeglicht Maskenannotation am Desktop, trainiert Segmentierungsmodelle und installiert Modelle fuer die PWA.

## Rolle Im Gesamtsystem

```text
PWA auf Smartphone
  Rohbilder sammeln
  Raw-ZIP exportieren

Trainer auf Desktop
  Raw-ZIP importieren
  Muenze markieren
  Daten pruefen und aufteilen
  Modell trainieren, testen und exportieren
  Modellpaket erstellen
  Modell in PWA uebernehmen

PWA
  Scan-Modell in Einstellungen auswaehlen
  ONNX-Modell lokal fuer Scan nutzen
```

## Technische Entscheidungen

| Bereich | Entscheidung |
|---|---|
| Sprache | Python 3.12 |
| Desktop UI | PySide6 |
| CLI | Typer + Rich |
| Training | PyTorch |
| Bildverarbeitung | Pillow, OpenCV, NumPy |
| Augmentierung | Albumentations |
| Export | ONNX, ONNX Runtime, ONNX Simplifier |
| Zielplattform | Windows zuerst |
| GPU | erlaubt, CPU-Fallback sinnvoll |
| Online im Training | erlaubt |
| PWA Runtime | bleibt offlinefaehig |

## Aktueller Stand

Alle geplanten Phasen sind umgesetzt und verifiziert. Der Trainer ist als Python-3.12-Paket `mcs_trainer` pip-installierbar (editable). CLI, ML-Pipeline und PySide6-GUI sind end-to-end getestet.

CLI-Befehle (alle funktionstuechtig):

- `mcs-trainer import-raw --zip <zip> [--dest trainer/data/raw]`
- `mcs-trainer validate --dataset <dir> [--mode auto|raw|annotated]`
- `mcs-trainer split --dataset <dir> [--train 0.8] [--val 0.1] [--test 0.1] [--seed 42]`
- `mcs-trainer train --dataset <dir> --profile general [--device auto|cuda|cpu] [--epochs 30] [--batch-size 8] [--lr 1e-3] [--seed 42] [--out-dir trainer/runs/coinseg]`
- `mcs-trainer evaluate --run <run> --dataset <dir> [--device auto]`
- `mcs-trainer export-onnx --run <run> [--opset 17]`
- `mcs-trainer package-model --onnx <onnx> --run <run> [--out-dir trainer/model-packages]`
- `mcs-trainer gui [--dataset <dir>]`

Tests: 28 Tests via `python -m pytest -q` aus `trainer/` gruen. Decken Import, Raw-/Annotated-Validierung, Splits und CLI-Smoke ab.

End-to-end Smoke verifiziert: validate -> split (8/1/1) -> train (5 Epochen, val dice 0.99) -> evaluate (test dice 0.99) -> export-onnx (Input [1,3,512,512], Output [1,1,512,512], Bereich 0..1) -> package-model -> Modell in PWA uebernommen.

PWA-Modellverwaltung: Modelle liegen unter `wwwroot/models/<model-id>/`. `wwwroot/models/manifest.json` verwendet `schemaVersion = mcs-model-index-v1`. Vor Ersatz vorhandener Modelle erstellt die GUI nach Bestaetigung Backups. Die PWA bietet in den Einstellungen eine Scan-Modell-Auswahl aus dem Manifest und faellt ohne Manifest auf `wwwroot/models/coin-segmentation.onnx` zurueck.

## Ordnerstruktur

```text
trainer/
  pyproject.toml
  README.md
  PROJEKTUEBERSICHT.md
  trainer_plan.md
  docs/
    gui.md
    model-management.md
  src/mcs_trainer/
    __init__.py            (__version__ = "0.1.0")
    __main__.py
    utils/
      paths.py             (safe_join, resolve_dataset_dir, ensure_subdirs, slugify_dataset_id)
    dataset/
      schemas.py           (Pydantic v2: Raw/Annotated Metadata+Sample, Schema-Versionen)
      raw_zip.py           (import_raw_zip -> RawImportResult)
      annotated_dataset.py (load_annotated, save_annotated, create_annotated_skeleton)
      splits.py            (make_split -> SplitResult, 80/10/10, seed 42, excludes)
      validation.py        (validate_raw, validate_annotated -> ValidationResult)
    cli/
      main.py              (typer app, 8 Befehle, lazy ML/GUI imports)
    ml/
      model.py             (build_model -> U-Net, base=32, sigmoid output)
      augmentations.py     (get_train/val_transforms, direct-stretch 512x512)
      dataset.py           (CoinSegDataset)
      metrics.py           (dice_score, iou_score)
      train_loop.py        (TrainConfig, train(), evaluate(), Checkpoints, metrics.json/run.json/eval.json)
      onnx_export.py       (export_onnx, validate_onnx; feste Shapes, onnxsim)
      package_model.py     (package_model: zip mit onnx/model.json/metrics.json/preprocessing.json/README/SHA256SUMS)
    app/
      main.py              (main(), gui() Entry Points)
      image_viewer.py      (ImageViewer: Zoom/Pan, Pinsel/Radierer/Ellipse)
      mask_editor.py       (MaskEditor: Undo/Redo, to_mask_png_bytes 8-bit L {0,255})
      metadata_panel.py    (MetadataPanel: notes/tags/excluded)
      main_window.py       (MainWindow: Toolbar, 3-Pane, Tastatur-Navigation, Workflow-Aktionen, QProcess-Training/Export)
  tests/                   (28 Tests: Import, Raw-/Annotated-Validierung, Splits, CLI-Smoke)
  data/
    incoming/
    raw/
    annotated/
  runs/
  exports/
  model-packages/
```

## Datenformate

### Raw-ZIP Aus PWA

```text
mcs-raw-images-v1.zip
  images/
  metadata.json
```

### Annotated Dataset

```text
mcs-annotated-dataset-v1.zip
  images/
  masks/
  metadata.json
  splits/
    train.txt
    val.txt
    test.txt
```

Masken:

- PNG
- 8-bit Graustufen
- gleiche Groesse wie Originalbild
- `0 = Hintergrund`
- `255 = Muenze`

## Desktop-GUI

- Raw-ZIP importieren
- Bildliste
- Bildviewer mit Zoom/Pan
- Tastatur-Navigation
- Pinsel und Radierer
- Kreis/Ellipse als Startform
- Undo/Redo
- Metadatenpanel
- Ausschluss einzelner Bilder
- Dataset-Speicherung
- Annotated-Dataset-Export
- Daten pruefen
- Daten aufteilen
- Trainingslauf mit Konfiguration starten
- Modell testen
- ONNX exportieren
- Modellpaket erstellen
- Modell in PWA uebernehmen
- Trainingslog anzeigen

## CLI MVP

- `import-raw`
- `validate`
- `split`
- `train`
- `evaluate`
- `export-onnx`
- `package-model`

## Trainingsziele

Profile:

- `general`
- `poker-coins`
- `silver-dollar`
- `stage-light`
- `customer-*`

Modellvertrag fuer PWA:

```text
input:  float32[1,3,512,512], RGB, 0..1
output: float32[1,1,512,512], 0..1
threshold: 0.5
```

## Modellverwaltung Fuer Die PWA

- Installationsziel: `wwwroot/models/<model-id>/`.
- Modellindex: `wwwroot/models/manifest.json` mit `schemaVersion = mcs-model-index-v1`.
- PWA Settings: Scan-Modell aus dem Manifest auswaehlen.
- Legacy-Fallback: `wwwroot/models/coin-segmentation.onnx`, falls kein Manifest verfuegbar ist.
- Ersatz vorhandener Modelle erfolgt in der GUI erst nach Bestaetigung und mit Backup.

## Naechste Schritte

- Smoke-Test-Modell durch ein mit echten Muenzbildern trainiertes Produktionsmodell ersetzen.
- Weitere Trainingsprofile (`poker-coins`, `silver-dollar`, `stage-light`, `customer-*`) implementieren.
- Smartere Splits: gleiche Muenze/Session nicht gleichzeitig in Train und Test.
- PWA-Smoke-Test Automation gegen Manifest-Modell und Legacy-Fallback.
- GUI Active-Learning Verbesserungen (z. B. Vorhersage-basiertes Vorannotieren).
- Produktionsmodell mit echten Muenzbildern trainieren und in PWA ausliefern.
