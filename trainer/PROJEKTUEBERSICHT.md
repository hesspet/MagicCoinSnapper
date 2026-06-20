# Projektuebersicht - MagicCoinSnapper Trainer

## Kurzprofil

Der MagicCoinSnapper Trainer ist eine lokale Desktop-/CLI-Anwendung fuer Windows. Er verarbeitet Rohbilder aus der MagicCoinSnapper PWA, ermoeglicht Maskenannotation am Desktop und erzeugt Trainingsdaten sowie ONNX-Modelle fuer die PWA.

## Rolle Im Gesamtsystem

```text
PWA auf Smartphone
  Rohbilder sammeln
  Raw-ZIP exportieren

Trainer auf Desktop
  Raw-ZIP importieren
  Muenze markieren
  Metadaten pflegen
  Dataset validieren
  Modell trainieren
  ONNX exportieren

PWA
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

## Geplante Ordnerstruktur

```text
trainer/
  pyproject.toml
  README.md
  PROJEKTUEBERSICHT.md
  trainer_plan.md
  src/mcs_trainer/
    app/
    cli/
    dataset/
    ml/
    utils/
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

## Desktop-App MVP

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
- Trainingslauf starten
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

## Naechste Session

Mit dem CLI-Kern starten:

1. Python-Projekt initialisieren.
2. Dependencies minimal halten.
3. `mcs-trainer` CLI bereitstellen.
4. Raw-ZIP-Import implementieren.
5. Dataset-Schema per Pydantic definieren.
6. Validierung implementieren.
7. Erste Tests fuer Import und Schema schreiben.
