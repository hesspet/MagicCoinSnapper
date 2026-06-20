# Trainer-Plan

Dieses Dokument beschreibt den geplanten Desktop-/CLI-Trainer fuer MagicCoinSnapper.

## Ziel

Die PWA bleibt die Vorfuehr- und Sammel-App. Sie sammelt Rohbilder auf dem Smartphone und exportiert ein ZIP.

Der Trainer laeuft lokal auf dem Desktop, zuerst Windows-only. Dort werden Bilder gesichtet, Masken gezeichnet, Metadaten gepflegt, Trainingslaeufe gestartet und ONNX-Modelle erzeugt.

## Entscheidungen

- Technologie: Python 3.12
- Desktop UI: PySide6
- CLI: Typer + Rich
- Training: PyTorch
- GPU: darf genutzt werden, CPU-Fallback bleibt sinnvoll
- ONNX: Export kompatibel zur PWA
- Modellinput vorerst: 512x512
- Training darf Online-Komponenten nutzen, z. B. Pretrained Weights oder Downloads
- PWA bleibt im Showbetrieb offlinefaehig

## Datenfluss

```text
MagicCoinSnapper PWA
  -> mcs-raw-images-v1.zip

MagicCoinSnapper Trainer
  -> Import
  -> Annotation
  -> Metadaten
  -> mcs-annotated-dataset-v1.zip

Training Pipeline
  -> PyTorch Training
  -> Evaluation
  -> ONNX Export
  -> Modellpaket

MagicCoinSnapper PWA
  -> wwwroot/models/coin-segmentation.onnx
```

## Geplante Struktur

```text
trainer/
  pyproject.toml
  README.md
  PROJEKTUEBERSICHT.md
  trainer_plan.md
  src/mcs_trainer/
    app/
      main.py
      main_window.py
      image_viewer.py
      mask_editor.py
      metadata_panel.py
    cli/
      main.py
      import_raw.py
      validate_dataset.py
      train.py
      export_onnx.py
      package_model.py
    dataset/
      raw_zip.py
      annotated_dataset.py
      schemas.py
      splits.py
    ml/
      model.py
      train_loop.py
      augmentations.py
      metrics.py
      onnx_export.py
    utils/
      image_io.py
      paths.py
  data/
    incoming/
    raw/
    annotated/
  runs/
  exports/
  model-packages/
```

## Raw-ZIP Aus Der PWA

```text
mcs-raw-images-v1.zip
  images/
    sample-0001.jpg
    sample-0002.png
  metadata.json
```

## Annotiertes Dataset

```text
mcs-annotated-dataset-v1.zip
  images/
    sample-0001.jpg
  masks/
    sample-0001.png
  metadata.json
  splits/
    train.txt
    val.txt
    test.txt
```

Maskenformat:

- PNG
- 8-bit Graustufen
- gleiche Groesse wie Originalbild
- `0 = Hintergrund`
- `255 = Muenze`

## Desktop-App MVP

- Raw-ZIP importieren
- Bildliste anzeigen
- Bildviewer mit Zoom/Pan
- Vor/zurueck per Tastatur
- Maske zeichnen
- Radierer
- Kreis/Ellipse als Startform
- Undo/Redo
- Bild ausschliessen
- Metadaten pflegen
- Dataset validieren
- Annotated Dataset exportieren
- Trainingslauf starten
- Trainingslog anzeigen
- ONNX exportieren

## CLI MVP

```pwsh
mcs-trainer import-raw --zip .\data\incoming\mcs-raw-images.zip
mcs-trainer validate --dataset .\data\annotated\coins-v1
mcs-trainer split --dataset .\data\annotated\coins-v1
mcs-trainer train --dataset .\data\annotated\coins-v1 --profile general --device cuda
mcs-trainer evaluate --run .\runs\coinseg\general-001
mcs-trainer export-onnx --run .\runs\coinseg\general-001
mcs-trainer package-model --onnx .\exports\coin-segmentation.onnx
```

## Trainingsprofile

- `general`: allgemeines Modell fuer viele Muenzen, Haende und Lichtbedingungen
- `poker-coins`: spezialisiert auf Pokermuenzen
- `silver-dollar`: spezialisiert auf bestimmte Muenztypen
- `stage-light`: spezialisiert auf Buehnenlicht
- `customer-*`: kundenspezifisches Fine-Tuning

## ONNX-Vertrag Mit Der PWA

```text
input:
  name: input
  shape: [1, 3, 512, 512]
  format: RGB
  dtype: float32
  range: 0..1

output:
  name: mask
  shape: [1, 1, 512, 512]
  range: 0..1
  meaning: Muenzwahrscheinlichkeit
  threshold: 0.5
```

## Modellpaket

```text
mcs-model-general-1.0.0.zip
  coin-segmentation.onnx
  model.json
  metrics.json
  preprocessing.json
  README.md
  SHA256SUMS.txt
```

## Umsetzungsphasen

1. `trainer/` Python-Projekt anlegen. [erledigt] Paket `mcs_trainer`, `pyproject.toml`, editable installiert.
2. CLI-Grundlage mit Raw-ZIP-Import bauen. [erledigt] `import-raw` per Typer, `raw_zip.py`.
3. Dataset-Schema und Validierung implementieren. [erledigt] Pydantic-v2-Schemas, `validate` fuer raw + annotated.
4. PySide6-Bildviewer bauen. [erledigt] `ImageViewer` mit Zoom/Pan.
5. Maskenwerkzeuge hinzufuegen. [erledigt] Pinsel/Radierer/Ellipse, Undo/Redo, `MaskEditor`.
6. Metadatenpanel und Dataset-Speicherung ergaenzen. [erledigt] `MetadataPanel` (notes/tags/excluded), `annotated_dataset.py`.
7. Trainingspipeline mit PyTorch bauen. [erledigt] U-Net (base=32), `train`/`evaluate`, BCE+Adam, Checkpoints.
8. ONNX-Export und ONNX-Validierung ergaenzen. [erledigt] `export-onnx`, feste Shapes [1,3,512,512]->[1,1,512,512], onnxsim.
9. Modellpaket-Erzeugung bauen. [erledigt] `package-model`, zip mit onnx/model.json/metrics.json/preprocessing.json/README/SHA256SUMS.
10. PWA-Smoke-Test mit `wwwroot/models/coin-segmentation.onnx`. [erledigt] ONNX kopiert; aktuell Smoke-Modell, noch kein Produktionsmodell.

## Status

Alle 10 Phasen sind abgeschlossen und verifiziert. Die CLI hat 8 Befehle (`import-raw`, `validate`, `split`, `train`, `evaluate`, `export-onnx`, `package-model`, `gui`). 28 Tests via `python -m pytest -q` aus `trainer/` gruen. End-to-end-Smoke verifiziert: validate -> split (8/1/1) -> train (5 Epochen, val dice 0.99) -> evaluate (test dice 0.99) -> export-onnx (Input [1,3,512,512], Output [1,1,512,512], 0..1) -> package-model -> ONNX nach `wwwroot/models/coin-segmentation.onnx`.

## Naechste Schritte

- Smoke-Test-ONNX durch ein mit echten Muenzbildern trainiertes Produktionsmodell ersetzen.
- Weitere Trainingsprofile implementieren (`poker-coins`, `silver-dollar`, `stage-light`, `customer-*`).
- Smartere Splits: gleiche Muenze/Session nicht gleichzeitig in Train und Test.
- GUI Active-Learning Verbesserungen.
- Produktionsmodell mit echten Muenzbildern trainieren und in PWA ausliefern.
