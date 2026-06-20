from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from mcs_trainer import __version__
from mcs_trainer.dataset.raw_zip import import_raw_zip
from mcs_trainer.dataset.splits import make_split
from mcs_trainer.dataset.validation import (
    validate_annotated,
    validate_raw,
)

app = typer.Typer(
    name="mcs-trainer",
    help="MagicCoinSnapper Trainer CLI",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"mcs-trainer {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Version anzeigen und beenden.",
    ),
) -> None:
    """MagicCoinSnapper Trainer CLI."""


@app.command("import-raw")
def import_raw_cmd(
    zip: Path = typer.Option(..., "--zip", help="Pfad zur PWA-Roh-ZIP."),
    dest: Path = typer.Option(
        Path("trainer/data/raw"),
        "--dest",
        help="Zielverzeichnis für Roh-Datasets.",
    ),
) -> None:
    """Importiert eine PWA-Roh-ZIP in ein normiertes Verzeichnis."""
    result = import_raw_zip(zip, dest)
    table = Table(title="Import-Ergebnis")
    table.add_column("Feld", style="cyan")
    table.add_column("Wert", style="white")
    table.add_row("Dataset-ID", result.dataset_id)
    table.add_row("Verzeichnis", str(result.dataset_dir))
    table.add_row("Bilder", str(result.image_count))
    table.add_row("Warnungen", str(len(result.warnings)))
    console.print(table)
    for w in result.warnings:
        console.print(f"[yellow]![/yellow] {w}")


@app.command("validate")
def validate_cmd(
    dataset: Path = typer.Option(..., "--dataset", help="Dataset-Verzeichnis."),
    mode: str = typer.Option(
        "auto", "--mode", help="auto|raw|annotated"
    ),
) -> None:
    """Validiert ein Raw- oder Annotated-Dataset."""
    import json

    meta_path = dataset / "metadata.json"
    if not meta_path.exists():
        console.print(f"[red]Fehler:[/red] metadata.json fehlt: {meta_path}")
        raise typer.Exit(1)

    try:
        raw_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        console.print(f"[red]Fehler:[/red] metadata.json ungültig: {exc}")
        raise typer.Exit(1) from exc

    schema = raw_meta.get("schemaVersion", "")
    chosen = mode
    if mode == "auto":
        if schema == "mcs-raw-images-v1":
            chosen = "raw"
        elif schema == "mcs-annotated-dataset-v1":
            chosen = "annotated"
        else:
            console.print(
                f"[red]Fehler:[/red] SchemaVersion unbekannt: '{schema}'"
            )
            raise typer.Exit(1)

    if chosen == "raw":
        res = validate_raw(dataset)
    elif chosen == "annotated":
        res = validate_annotated(dataset)
    else:
        console.print(f"[red]Fehler:[/red] Unbekannter Modus: {chosen}")
        raise typer.Exit(1)

    console.print(f"Modus: [cyan]{chosen}[/cyan]")
    if res.errors:
        console.print(f"[red]{len(res.errors)} Fehler[/red]")
        for e in res.errors:
            console.print(f"[red]x[/red] {e}")
    else:
        console.print("[green]Keine Fehler.[/green]")
    if res.warnings:
        console.print(f"[yellow]{len(res.warnings)} Warnungen[/yellow]")
        for w in res.warnings:
            console.print(f"[yellow]![/yellow] {w}")

    if not res.ok:
        raise typer.Exit(1)


@app.command("split")
def split_cmd(
    dataset: Path = typer.Option(..., "--dataset", help="Dataset-Verzeichnis."),
    train: float = typer.Option(0.8, "--train", help="Train-Anteil."),
    val: float = typer.Option(0.1, "--val", help="Val-Anteil."),
    test: float = typer.Option(0.1, "--test", help="Test-Anteil."),
    seed: int = typer.Option(42, "--seed", help="Seed für Shuffle."),
) -> None:
    """Erstellt Train/Val/Test-Splits."""
    result = make_split(dataset, train_ratio=train, val_ratio=val, test_ratio=test, seed=seed)
    table = Table(title="Split-Ergebnis")
    table.add_column("Split", style="cyan")
    table.add_column("Anzahl", style="white")
    table.add_row("Train", str(result.train_count))
    table.add_row("Val", str(result.val_count))
    table.add_row("Test", str(result.test_count))
    console.print(table)


_ML_MISSING_MSG = "ML-Abhaengigkeiten fehlen. Installiere mit: pip install -e .[ml]"


def _check_ml() -> None:
    try:
        import torch  # noqa: F401
    except Exception as exc:
        console.print(f"[red]Fehler:[/red] {_ML_MISSING_MSG}")
        raise typer.Exit(1) from exc


def _resolve_device(value: str) -> str:
    if value != "auto":
        return value
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


@app.command("train")
def train_cmd(
    dataset: Path = typer.Option(..., "--dataset", help="Dataset-Verzeichnis."),
    profile: str = typer.Option("general", "--profile", help="Profilname."),
    device: str = typer.Option("auto", "--device", help="auto|cuda|cpu."),
    epochs: int = typer.Option(30, "--epochs", help="Anzahl Epochs."),
    batch_size: int = typer.Option(8, "--batch-size", help="Batchgroesse."),
    lr: float = typer.Option(1e-3, "--lr", help="Lernrate."),
    seed: int = typer.Option(42, "--seed", help="Seed."),
    out_dir: Path = typer.Option(
        Path("trainer/runs/coinseg"), "--out-dir", help="Ausgabe-Verzeichnis."
    ),
) -> None:
    """Trainiert das Segmentierungsmodell."""
    _check_ml()
    from mcs_trainer.ml.train_loop import train as train_fn

    resolved = _resolve_device(device)
    result = train_fn(
        dataset_dir=dataset,
        profile=profile,
        device=resolved,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        seed=seed,
        out_dir=out_dir,
    )
    table = Table(title="Train-Ergebnis")
    table.add_column("Feld", style="cyan")
    table.add_column("Wert", style="white")
    table.add_row("Run-Verzeichnis", str(result.run_dir))
    table.add_row("Best Val Dice", f"{result.best_dice:.4f}")
    table.add_row("Best Val IoU", f"{result.best_iou:.4f}")
    table.add_row("Epochs", str(result.epochs_run))
    table.add_row("Device", resolved)
    console.print(table)


@app.command("evaluate")
def evaluate_cmd(
    run: Path = typer.Option(..., "--run", help="Run-Verzeichnis."),
    dataset: Path = typer.Option(..., "--dataset", help="Dataset-Verzeichnis."),
    device: str = typer.Option("auto", "--device", help="auto|cuda|cpu."),
) -> None:
    """Evaluiert das beste Modell auf dem Test-Split."""
    _check_ml()
    from mcs_trainer.ml.train_loop import evaluate as eval_fn

    resolved = _resolve_device(device)
    result = eval_fn(run_dir=run, dataset_dir=dataset, device=resolved)
    table = Table(title="Eval-Ergebnis")
    table.add_column("Feld", style="cyan")
    table.add_column("Wert", style="white")
    table.add_row("Loss", f"{result.loss:.4f}")
    table.add_row("Dice", f"{result.dice:.4f}")
    table.add_row("IoU", f"{result.iou:.4f}")
    table.add_row("Samples", str(result.n_samples))
    console.print(table)


@app.command("export-onnx")
def export_onnx_cmd(
    run: Path = typer.Option(..., "--run", help="Run-Verzeichnis."),
    opset: int = typer.Option(17, "--opset", help="ONNX-Opset."),
) -> None:
    """Exportiert das beste Modell nach ONNX."""
    _check_ml()
    from mcs_trainer.ml.onnx_export import export_onnx as export_fn

    onnx_path = export_fn(run_dir=run, opset=opset)
    console.print(f"ONNX exportiert: [cyan]{onnx_path}[/cyan]")
    from mcs_trainer.ml.onnx_export import validate_onnx

    info = validate_onnx(onnx_path)
    table = Table(title="ONNX-Validierung")
    table.add_column("Feld", style="cyan")
    table.add_column("Wert", style="white")
    table.add_row("Input", f"{info['inputName']} {info['inputShape']}")
    table.add_row("Output", f"{info['outputName']} {info['outputShape']}")
    table.add_row("Output Min/Max", f"{info['outputMin']:.4f} / {info['outputMax']:.4f}")
    console.print(table)


@app.command("package-model")
def package_model_cmd(
    onnx: Path = typer.Option(..., "--onnx", help="Pfad zur ONNX-Datei."),
    run: Path = typer.Option(..., "--run", help="Run-Verzeichnis."),
    out_dir: Path = typer.Option(
        Path("trainer/model-packages"),
        "--out-dir",
        help="Zielverzeichnis fuer Paket.",
    ),
) -> None:
    """Packt Modell + Metadaten in ein ZIP-Paket."""
    _check_ml()
    from mcs_trainer.ml.package_model import package_model as pkg_fn

    zip_path = pkg_fn(onnx_path=onnx, run_dir=run, out_dir=out_dir)
    console.print(f"Paket erstellt: [cyan]{zip_path}[/cyan]")


@app.command("gui")
def gui_cmd(
    dataset: Optional[Path] = typer.Option(
        None, "--dataset", help="Annotated-Dataset direkt oeffnen."
    ),
) -> None:
    """Startet die PySide6-Trainings-GUI."""
    try:
        from mcs_trainer.app.main import main as gui_main
    except ImportError:
        console.print(
            "[red]GUI-Abhaengigkeiten fehlen. Installiere mit: pip install -e .[gui]"
        )
        raise typer.Exit(1)
    if dataset is not None:
        gui_main(["--dataset", str(dataset)])
    else:
        gui_main()
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
