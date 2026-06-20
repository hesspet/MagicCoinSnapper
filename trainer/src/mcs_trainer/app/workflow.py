from __future__ import annotations

from pathlib import Path

from mcs_trainer.dataset.splits import SplitResult, make_split
from mcs_trainer.dataset.validation import ValidationResult, validate_annotated
from mcs_trainer.ml.model_registry import (
    InstallResult,
    build_model_metadata,
    install_model_into_pwa,
    model_install_targets_exist,
)


def validate_annotated_dataset(dataset_dir: Path) -> ValidationResult:
    return validate_annotated(Path(dataset_dir))


def split_dataset(
    dataset_dir: Path,
    train: float = 0.8,
    val: float = 0.1,
    test: float = 0.1,
    seed: int = 42,
) -> SplitResult:
    return make_split(Path(dataset_dir), train_ratio=train, val_ratio=val, test_ratio=test, seed=seed)


def evaluate_model(run_dir: Path, dataset_dir: Path, device: str = "auto"):
    from mcs_trainer.ml.train_loop import evaluate

    return evaluate(run_dir=Path(run_dir), dataset_dir=Path(dataset_dir), device=device)


def export_onnx_model(run_dir: Path, opset: int = 17) -> Path:
    from mcs_trainer.ml.onnx_export import export_onnx

    return export_onnx(run_dir=Path(run_dir), opset=opset)


def package_trained_model(
    *,
    onnx_path: Path,
    run_dir: Path,
    out_dir: Path = Path("trainer/model-packages"),
    metadata: dict | None = None,
) -> Path:
    from mcs_trainer.ml.package_model import package_model

    return package_model(
        onnx_path=Path(onnx_path),
        run_dir=Path(run_dir),
        out_dir=Path(out_dir),
        metadata=metadata,
    )


def install_model(
    *,
    onnx_path: Path,
    pwa_wwwroot: Path,
    metadata: dict,
    backup_existing: bool = True,
) -> InstallResult:
    return install_model_into_pwa(
        onnx_path=Path(onnx_path),
        pwa_wwwroot=Path(pwa_wwwroot),
        metadata=metadata,
        backup_existing=backup_existing,
    )


def find_newest_run(out_dir: Path = Path("trainer/runs/coinseg"), profile: str | None = None) -> Path | None:
    root = Path(out_dir)
    if not root.is_dir():
        return None
    candidates = [p for p in root.iterdir() if p.is_dir()]
    if profile:
        candidates = [p for p in candidates if p.name.startswith(f"{profile}-")]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def default_pwa_wwwroot() -> Path:
    for base in [Path.cwd(), *Path.cwd().parents]:
        candidate = base / "wwwroot"
        if candidate.is_dir():
            return candidate
    return Path("wwwroot")


__all__ = [
    "build_model_metadata",
    "default_pwa_wwwroot",
    "evaluate_model",
    "export_onnx_model",
    "find_newest_run",
    "install_model",
    "model_install_targets_exist",
    "package_trained_model",
    "split_dataset",
    "validate_annotated_dataset",
]
