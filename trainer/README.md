# MagicCoinSnapper Trainer

## 1. Kurzbeschreibung

Der Trainer ist die lokale Desktop-/CLI-Komponente von MagicCoinSnapper. Die Smartphone-PWA sammelt Rohbilder und exportiert eine Raw-ZIP. Der Trainer importiert diese ZIP, erlaubt Maskenannotation am Desktop, validiert die Datasets, trainiert ein Segmentierungsmodell und exportiert ONNX fuer die PWA.

Die Umsetzung erfolgt in Phasen. Verfuegbar sind jetzt:
- CLI-Kern: `import-raw`, `validate`, `split`
- ML-Pipeline: `train`, `evaluate`, `export-onnx`, `package-model`
- PySide6-Annotationsoberflaeche: `mcs-trainer gui`

## 2. Voraussetzungen

- Python 3.12 oder neuer
- Windows wird zuerst unterstuetzt; CPU-Fallback bleibt sinnvoll

Installation im Trainer-Verzeichnis:

```pwsh
cd trainer
python -m pip install -e .
```

Optionale Abhaengigkeitsgruppen aus `pyproject.toml`:

```pwsh
python -m pip install -e .[dev]    # pytest>=8
python -m pip install -e .[ml]     # torch, torchvision, albumentations, onnx, onnxruntime, onnxsim
python -m pip install -e .[gui]    # PySide6
```

Der CLI-Einstieg ist via `mcs-trainer` registriert (`[project.scripts]`). Version anzeigen:

```pwsh
mcs-trainer --version
```

## 3. Schnellstart

Minimale Befehlsfolge vom PWA-Export bis zum fertigen Split:

1. PWA-Raw-ZIP in `trainer/data/incoming/` ablegen.
2. Raw-ZIP importieren:

   ```pwsh
   mcs-trainer import-raw --zip .\data\incoming\mcs-raw-images-2026-06-20.zip
   ```

3. Roh-Dataset validieren:

   ```pwsh
   mcs-trainer validate --dataset .\data\raw\<datasetId>
   ```

4. Bilder annotieren (ueber `mcs-trainer gui` oder manuell), dann annotated-Dataset validieren:

   ```pwsh
   mcs-trainer validate --dataset .\data\annotated\coins-v1
   ```

5. Splits erzeugen:

   ```pwsh
   mcs-trainer split --dataset .\data\annotated\coins-v1
   ```

## 4. Befehle im Detail

Alle Befehle werden via `mcs-trainer <command>` aufgerufen. Es gibt keinen Default-Subcommand; Aufruf ohne Argumente zeigt die Hilfe.

### import-raw

Importiert eine PWA-Roh-ZIP in ein normiertes Verzeichnis unter `--dest/<datasetId>/`.

| Flag | Typ | Default | Beschreibung |
|---|---|---|---|
| `--zip` | Path | erforderlich | Pfad zur PWA-Roh-ZIP. |
| `--dest` | Path | `trainer/data/raw` | Zielverzeichnis fuer Roh-Datasets. |

Beispiel:

```pwsh
mcs-trainer import-raw --zip .\data\incoming\mcs-raw-images-2026-06-20.zip --dest .\data\raw
```

Verhalten:
- Liest `metadata.json` aus der ZIP, validiert sie gegen `RawMetadata` (`schemaVersion = mcs-raw-images-v1`).
- Legt Bilder unter `<dest>/<datasetId>/images/` ab.
- Doppelte Sample-IDs werden ignoriert (Warnung).
- Pro Bild werden Pillow-Verifikation sowie Abgleich von `width`, `height`, `contentType` und `sizeBytes` gegen die tatsaechliche Datei durchgefuehrt; Abweichungen landen als Warnungen.
- Schreibt eine normalisierte `metadata.json` (ohne Duplikate) ins Zielverzeichnis.

Ausgabe (Konsole): Tabelle mit `Dataset-ID`, `Verzeichnis`, `Bilder`, `Warnungen` sowie einzelne Warnungszeilen.

Erzeugtes Layout:

```text
trainer/data/raw/<datasetId>/
  images/
    <bild>.jpg
  metadata.json
```

### validate

Validiert ein Raw- oder Annotated-Dataset. Der Modus wird aus `schemaVersion` in `metadata.json` abgeleitet, sofern nicht explizit gesetzt.

| Flag | Typ | Default | Beschreibung |
|---|---|---|---|
| `--dataset` | Path | erforderlich | Dataset-Verzeichnis. |
| `--mode` | str | `auto` | `auto`, `raw` oder `annotated`. Bei `auto` wird das Schema erkannt (`mcs-raw-images-v1` -> `raw`, `mcs-annotated-dataset-v1` -> `annotated`). |

Beispiel (Raw):

```pwsh
mcs-trainer validate --dataset .\data\raw\mcs-raw-images-2026-06-20 --mode raw
```

Beispiel (Annotated, Auto-Erkennung):

```pwsh
mcs-trainer validate --dataset .\data\annotated\coins-v1
```

Verhalten fuer `raw`:
- Prueft `metadata.json` gegen `RawMetadata` und `schemaVersion = mcs-raw-images-v1`.
- Pro Sample: Existenz und Lesbarkeit des Bilds; optionale `width`/`height`-Warnungen bei Mismatch.

Verhalten fuer `annotated`:
- Prueft `metadata.json` gegen `AnnotatedMetadata` und `schemaVersion = mcs-annotated-dataset-v1`.
- Prueft `splits/train.txt`, `val.txt`, `test.txt` (fehlende Dateien sind Warnungen). Split-IDs muessen bekannten Samples zugeordnet werden koennen; ausgeschlossene Samples (`excluded = true`) duerfen in keinem Split stehen.
- Pro Sample: Existenz und Lesbarkeit von Bild und Maske; Maske muss PNG im Modus `L` (8-bit Graustufen) sein; Maskenwerte muessen in `{0, 255}` liegen; Maskendimensionen muessen mit dem Bild uebereinstimmen; `metadata.width/height`-Mismatch gegen Maske ist eine Warnung.

Ausgabe: Modus, Anzahl Fehler und Warnungen, einzelne Meldungen. Bei Fehlern beendet sich der Befehl mit Exit-Code 1.

### split

Erstellt Train/Val/Test-Splits fuer ein annotated-Dataset und schreibt sie nach `<dataset>/splits/`.

| Flag | Typ | Default | Beschreibung |
|---|---|---|---|
| `--dataset` | Path | erforderlich | Annotated-Dataset-Verzeichnis. |
| `--train` | float | `0.8` | Train-Anteil. |
| `--val` | float | `0.1` | Val-Anteil. |
| `--test` | float | `0.1` | Test-Anteil. |
| `--seed` | int | `42` | Seed fuer Shuffle. |

Die Anteile muessen sich zu `1.0` addieren (Toleranz `1e-6`) und duerfen nicht negativ sein. Ausgeschlossene Samples (`excluded = true`) werden vor dem Split herausgefiltert. Shuffle und anschliessende Aufteilung: `n_train = round(n * train)`, `n_val = round(n * val)`, `n_test = n - n_train - n_val` (mindestens 0).

Beispiel:

```pwsh
mcs-trainer split --dataset .\data\annotated\coins-v1 --train 0.8 --val 0.1 --test 0.1 --seed 42
```

Ausgabe: Tabelle mit Train-/Val-/Test-Anzahlen.

Erzeugte Dateien:

```text
<dataset>/splits/train.txt
<dataset>/splits/val.txt
<dataset>/splits/test.txt
```

Format: eine Sample-ID pro Zeile, UTF-8.

### train

Trainiert das Segmentierungsmodell (U-Net) auf einem annotated-Dataset mit vorhandenen Splits. Benoetigt die ML-Abhaengigkeiten (`pip install -e .[ml]`).

| Flag | Typ | Default | Beschreibung |
|---|---|---|---|
| `--dataset` | Path | erforderlich | Annotated-Dataset-Verzeichnis. |
| `--profile` | str | `general` | Trainingsprofil (`general`, `poker-coins`, `silver-dollar`, `stage-light`, `customer-*`). |
| `--device` | str | `auto` | `auto` (CUDA falls verfuegbar sonst CPU), `cuda` oder `cpu`. |
| `--epochs` | int | `30` | Anzahl Epochen. |
| `--batch-size` | int | `8` | Batch-Groesse. |
| `--lr` | float | `1e-3` | Lernrate (Adam). |
| `--seed` | int | `42` | Seed fuer Reproduzierbarkeit. |
| `--out-dir` | Path | `trainer/runs/coinseg` | Wurzel fuer Run-Verzeichnisse. |

Beispiel:

```pwsh
mcs-trainer train --dataset .\data\annotated\coins-v1 --profile general --epochs 30 --device cuda
```

Verhalten:
- Preprocessing exakt wie die PWA: direktes Resize auf 512x512 (Stretch, kein Letterboxing), RGB, Normalisierung auf `0..1`. Maske `{0,255}` -> `{0.0,1.0}`.
- Verlust: BCEWithLogits; Optimizer: Adam; Metriken: Dice/IoU (Threshold 0.5).
- Speichert `checkpoints/best.pt` (nach Val-Dice) und `checkpoints/last.pt`.
- Schreibt `metrics.json` (pro Epoche) und `run.json` (Config + Best-Metriken).
- Run-Verzeichnis wird automatisch durchnummeriert: `<out-dir>/<profile>-NNN`.

Ausgabe: Tabelle mit Run-Verzeichnis, Best Val Dice/IoU, Epochs, Device.

### evaluate

Evaluiert das beste Modell eines Runs auf dem Test-Split.

| Flag | Typ | Default | Beschreibung |
|---|---|---|---|
| `--run` | Path | erforderlich | Run-Verzeichnis (enth. `checkpoints/best.pt`). |
| `--dataset` | Path | erforderlich | Annotated-Dataset-Verzeichnis mit Test-Split. |
| `--device` | str | `auto` | `auto`, `cuda` oder `cpu`. |

Beispiel:

```pwsh
mcs-trainer evaluate --run .\trainer\runs\coinseg\general-001 --dataset .\data\annotated\coins-v1
```

Schreibt `eval.json` ins Run-Verzeichnis. Ausgabe: Tabelle mit Loss, Dice, IoU, Samples.

### export-onnx

Exportiert das beste Modell eines Runs nach ONNX und validiert es gegen den PWA-Vertrag.

| Flag | Typ | Default | Beschreibung |
|---|---|---|---|
| `--run` | Path | erforderlich | Run-Verzeichnis (enth. `checkpoints/best.pt`). |
| `--opset` | int | `17` | ONNX-Opset. |

Beispiel:

```pwsh
mcs-trainer export-onnx --run .\trainer\runs\coinseg\general-001
```

Verhalten:
- Export mit festen Shapes: Input `input` `[1,3,512,512]`, Output `mask` `[1,1,512,512]` (kein dynamischer Batch).
- Vereinfachung via `onnxsim`, falls verfuegbar.
- Validierung mit `onnxruntime`: prueft Input-/Output-Namen und -Shapes und fuehrt einen Vorwaertslauf aus.
- ONNX-Datei: `<run>/coin-segmentation.onnx`.

Ausgabe: Pfad der ONNX-Datei und Validierungstabelle (Input, Output, Output Min/Max).

### package-model

Packt Modell und Metadaten in ein ZIP-Paket fuer die Auslieferung.

| Flag | Typ | Default | Beschreibung |
|---|---|---|---|
| `--onnx` | Path | erforderlich | Pfad zur `coin-segmentation.onnx`. |
| `--run` | Path | erforderlich | Run-Verzeichnis (fuer `metrics.json`). |
| `--out-dir` | Path | `trainer/model-packages` | Zielverzeichnis. |

Beispiel:

```pwsh
mcs-trainer package-model --onnx .\trainer\runs\coinseg\general-001\coin-segmentation.onnx --run .\trainer\runs\coinseg\general-001
```

Paketinhalt:

```text
mcs-model-<profile>-<version>.zip
  coin-segmentation.onnx
  model.json
  metrics.json
  preprocessing.json
  README.md
  SHA256SUMS.txt
```

`preprocessing.json` dokumentiert den PWA-Vertrag (Resize 512x512 Stretch, RGB, `/255`, Threshold 0.5).

### gui

Startet die PySide6-Annotationsoberflaeche. Benoetigt `pip install -e .[gui]`.

| Flag | Typ | Default | Beschreibung |
|---|---|---|---|
| `--dataset` | Path | keiner | Annotated-Dataset direkt beim Start oeffnen. |

Beispiel:

```pwsh
mcs-trainer gui
mcs-trainer gui --dataset .\data\annotated\coins-v1
```

Funktionen:
- Raw-ZIP importieren (erstellt ein annotated-Dataset mit leeren Masken).
- Bildliste mit Tastatur-Navigation (Links/Rechts).
- Bildviewer mit Zoom (Strg+Mausrad) und Pan.
- Werkzeuge: Pinsel (B), Radierer (E), Ellipse (O), Radius mit `[`/`]`.
- Undo/Redo (Strg+Z / Strg+Umschalt+Z).
- Metadatenpanel (Notizen, Tags, Bild ausschliessen).
- Dataset speichern (Strg+S): schreibt Masken als 8-bit-Graustufen-PNG `{0,255}` und `metadata.json`.
- Export als `mcs-annotated-dataset-<datasetId>.zip`.
- Validierung und Training starten (Training als Hintergrundprozess mit Log-Anzeige).

## 5. Workflow

End-to-End-Workflow von der PWA bis zum fertigen ONNX-Modell:

1. Rohbilder in der PWA sammeln.
2. Raw-ZIP aus der PWA exportieren (`mcs-raw-images-v1.zip`).
3. ZIP in `trainer/data/incoming/` kopieren.
4. `import-raw` ausfuehren -> `trainer/data/raw/<datasetId>/` mit `images/` und `metadata.json`.
5. `validate --mode raw` ausfuehren; Warnungen ggf. an der PWA-Export-Seite oder den Quelldaten beheben.
6. Bilder annotieren: eine Maske pro Bild. Entweder ueber `mcs-trainer gui` oder manuell. Das erwartete annotated-Verzeichnislayout ist:

   ```text
   trainer/data/annotated/<datasetId>/
     images/
     masks/
     metadata.json
     splits/
   ```

   Maskenformat: PNG, 8-bit Graustufen (`PIL`-Modus `L`), gleiche Groesse wie das Originalbild, Werte `0 = Hintergrund` und `255 = Muenze`. In `metadata.json` gilt `schemaVersion = mcs-annotated-dataset-v1` (Sample-Felder siehe Abschnitt 6).
7. `validate --mode annotated` (bzw. `--mode auto`) ausfuehren.
8. `split` ausfuehren -> `splits/train.txt`, `val.txt`, `test.txt`.
9. `train` ausfuehren -> `trainer/runs/coinseg/<profile>-NNN/` mit `checkpoints/best.pt`, `metrics.json`, `run.json`.
10. `evaluate` ausfuehren (optional) -> Test-Metriken in `eval.json`.
11. `export-onnx` ausfuehren -> `<run>/coin-segmentation.onnx` (validiert gegen PWA-Vertrag).
12. `package-model` ausfuehren -> `trainer/model-packages/mcs-model-<profile>-<version>.zip`.
13. ONNX nach `wwwroot/models/coin-segmentation.onnx` kopieren. Die PWA nutzt es automatisch beim naechsten Scan (Fallback ist die Kreis-/Kontur-Heuristik, falls die Datei fehlt).

## 6. Datenformate

### Raw-ZIP aus der PWA

Inhalt:

```text
mcs-raw-images-v1.zip
  images/
  metadata.json
```

`metadata.json`-Schema (`schemaVersion = mcs-raw-images-v1`):

```text
schemaVersion: str   # "mcs-raw-images-v1"
datasetId: str
exportedAt: datetime
source: str | null
samples: list[RawSample]
```

`RawSample`-Felder (keine zusaetzlichen Felder erlaubt):

```text
id, source, contentType, sizeBytes, width, height, createdAt,
notes, image, tags
```

`image` ist ein relativer Pfad in die ZIP (z. Bsp. `images/<bild>.jpg`).

### Annotated-Dataset

Verzeichnislayout:

```text
<datasetId>/
  images/
  masks/
  metadata.json
  splits/
    train.txt
    val.txt
    test.txt
```

`metadata.json`-Schema (`schemaVersion = mcs-annotated-dataset-v1`):

```text
schemaVersion: str   # "mcs-annotated-dataset-v1"
datasetId: str
createdAt: datetime
source: str | null
samples: list[AnnotatedSample]
```

`AnnotatedSample`-Felder (keine zusaetzlichen Felder erlaubt):

```text
id, image, mask, width, height, contentType, excluded, notes, tags
```

### Maskenregeln

- PNG, 8-bit Graustufen (`PIL`-Modus `L`).
- Gleiche Dimensionen wie das Originalbild.
- Werte strikt in `{0, 255}`: `0 = Hintergrund`, `255 = Muenze`.

### Splits-Format

Jede Datei enthaelt genau eine Sample-ID pro Zeile (UTF-8). Ausgeschlossene Samples (`excluded = true`) stehen nicht in Splits.

## 7. Verzeichnisstruktur

Geplante Struktur des `trainer/`-Verzeichnisses (gem. PROJEKTUEBERSICHT.md):

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
    incoming/      # Roh-ZIPs aus der PWA
    raw/           # importierte Roh-Datasets
    annotated/     # annotierte Datasets mit Masken und Splits
  runs/           # Trainingslaeufe
  exports/        # exportierte ONNX-Modelle
  model-packages/ # gepackte Modelle fuer PWA-Auslieferung
```

## 8. Naechste Schritte

Alle geplanten Phasen sind umgesetzt. Moegliche Weiterentwicklungen:

- Mehr Trainingsprofile und kundenspezifische Fine-Tuning-Workflows (`customer-*`).
- Intelligentere Splits (gleiche Muenze/Session nicht gleichzeitig in Train und Test).
- Bewertung gegen echte PWA-Bilder und Optimierung der Modellarchitektur/-groesse.
- Automatisierter PWA-Smoke-Test nach ONNX-Auslieferung.
- GUI-Erweiterungen: Bulk-Aktionen, Vorhersage-unterstuetzte Annotation (Active Learning).
