from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import torch
from torch.utils.data import DataLoader

from mcs_trainer.dataset.annotated_dataset import load_annotated
from mcs_trainer.ml.dataset import CoinSegDataset
from mcs_trainer.ml.metrics import dice_loss, dice_score, iou_score
from mcs_trainer.ml.model import build_model
from mcs_trainer.ml.progress import format_train_progress


@dataclass
class TrainConfig:
    epochs: int = 30
    batch_size: int = 8
    lr: float = 1e-3
    device: str = "auto"
    profile: str = "general"
    seed: int = 42
    out_dir: Path = field(default_factory=lambda: Path("trainer/runs/coinseg"))


@dataclass
class TrainResult:
    run_dir: Path
    best_dice: float
    best_iou: float
    epochs_run: int


@dataclass
class EvalResult:
    run_dir: Path
    loss: float
    dice: float
    iou: float
    n_samples: int


def _resolve_device(device: str) -> torch.device:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device)


def _read_split(dataset_dir: Path, name: str) -> list[str]:
    path = dataset_dir / "splits" / f"{name}.txt"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def _next_run_dir(out_dir: Path, profile: str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(rf"^{re.escape(profile)}-(\d+)\Z")
    max_n = 0
    for child in out_dir.iterdir():
        if child.is_dir():
            m = pattern.match(child.name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    n = max_n + 1
    return out_dir / f"{profile}-{n:03d}"


def _seed_everything(seed: int, device: torch.device) -> None:
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)


def _hybrid_loss(
    pred: torch.Tensor, target: torch.Tensor, bce: torch.nn.Module
) -> torch.Tensor:
    return bce(pred, target) + dice_loss(pred, target)


def train(
    dataset_dir: Path,
    profile: str,
    device: str,
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
    out_dir: Path,
    progress_callback: Callable[[str], None] | None = None,
) -> TrainResult:
    dataset_dir = Path(dataset_dir).resolve()
    dev = _resolve_device(device)
    _seed_everything(seed, dev)
    metadata = load_annotated(dataset_dir)
    train_ids = _read_split(dataset_dir, "train")
    val_ids = _read_split(dataset_dir, "val")
    if not train_ids:
        raise RuntimeError("Train-Split ist leer (splits/train.txt).")
    train_ds = CoinSegDataset(metadata, dataset_dir, train_ids, train=True)
    val_ds = CoinSegDataset(metadata, dataset_dir, val_ids, train=False) if val_ids else None
    train_dl = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, num_workers=0, drop_last=False
    )
    val_dl = (
        DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
        if val_ds is not None
        else None
    )

    model = build_model().to(dev)
    criterion = torch.nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    run_dir = _next_run_dir(out_dir, profile)
    ckpt_dir = run_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    best_dice = -1.0
    best_iou = -1.0
    epochs_run = 0
    history: list[dict[str, float]] = []
    started = time.perf_counter()

    for epoch in range(1, epochs + 1):
        epochs_run = epoch
        model.train()
        train_loss_sum = 0.0
        n_batches = 0
        for imgs, masks in train_dl:
            imgs = imgs.to(dev)
            masks = masks.to(dev)
            optimizer.zero_grad()
            preds = model(imgs)
            loss = _hybrid_loss(preds, masks, criterion)
            loss.backward()
            optimizer.step()
            train_loss_sum += float(loss.item())
            n_batches += 1
        train_loss = train_loss_sum / max(n_batches, 1)

        val_loss = float("nan")
        val_dice = float("nan")
        val_iou = float("nan")
        if val_dl is not None:
            model.eval()
            val_loss_sum = 0.0
            dice_sum = 0.0
            iou_sum = 0.0
            n_val = 0
            with torch.no_grad():
                for imgs, masks in val_dl:
                    imgs = imgs.to(dev)
                    masks = masks.to(dev)
                    preds = model(imgs)
                    val_loss_sum += float(_hybrid_loss(preds, masks, criterion).item())
                    dice_sum += float(dice_score(preds, masks).item())
                    iou_sum += float(iou_score(preds, masks).item())
                    n_val += 1
            val_loss = val_loss_sum / max(n_val, 1)
            val_dice = dice_sum / max(n_val, 1)
            val_iou = iou_sum / max(n_val, 1)

            if val_dice > best_dice:
                best_dice = val_dice
                best_iou = val_iou
                torch.save(
                    {"model_state": model.state_dict(), "epoch": epoch},
                    ckpt_dir / "best.pt",
                )

        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_dice": val_dice,
                "val_iou": val_iou,
            }
        )
        torch.save(
            {"model_state": model.state_dict(), "epoch": epoch},
            ckpt_dir / "last.pt",
        )
        if progress_callback is not None:
            elapsed_s = time.perf_counter() - started
            eta_s = (elapsed_s / epoch) * max(epochs - epoch, 0)
            progress_callback(
                format_train_progress(
                    epoch=epoch,
                    total=epochs,
                    train_loss=train_loss,
                    val_loss=val_loss,
                    val_dice=val_dice,
                    val_iou=val_iou,
                    elapsed_s=elapsed_s,
                    eta_s=eta_s,
                )
            )

    if best_dice < 0.0 and val_dl is None:
        torch.save(
            {"model_state": model.state_dict(), "epoch": epochs_run},
            ckpt_dir / "best.pt",
        )
        best_dice = float("nan")
        best_iou = float("nan")

    (run_dir / "metrics.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8"
    )
    run_meta = {
        "profile": profile,
        "config": {
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "device": str(dev),
            "seed": seed,
        },
        "best": {"dice": best_dice, "iou": best_iou},
        "epochs_run": epochs_run,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "datasetDir": str(dataset_dir),
    }
    (run_dir / "run.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")
    return TrainResult(
        run_dir=run_dir, best_dice=best_dice, best_iou=best_iou, epochs_run=epochs_run
    )


def evaluate(run_dir: Path, dataset_dir: Path, device: str) -> EvalResult:
    run_dir = Path(run_dir).resolve()
    dataset_dir = Path(dataset_dir).resolve()
    dev = _resolve_device(device)
    metadata = load_annotated(dataset_dir)
    test_ids = _read_split(dataset_dir, "test")
    if not test_ids:
        raise RuntimeError("Test-Split ist leer (splits/test.txt).")
    test_ds = CoinSegDataset(metadata, dataset_dir, test_ids, train=False)
    test_dl = DataLoader(test_ds, batch_size=1, shuffle=False, num_workers=0)

    model = build_model().to(dev)
    ckpt_path = run_dir / "checkpoints" / "best.pt"
    if not ckpt_path.exists():
        ckpt_path = run_dir / "checkpoints" / "last.pt"
    ckpt = torch.load(ckpt_path, map_location=dev)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    criterion = torch.nn.BCELoss()
    loss_sum = 0.0
    dice_sum = 0.0
    iou_sum = 0.0
    n = 0
    with torch.no_grad():
        for imgs, masks in test_dl:
            imgs = imgs.to(dev)
            masks = masks.to(dev)
            preds = model(imgs)
            loss_sum += float(_hybrid_loss(preds, masks, criterion).item())
            dice_sum += float(dice_score(preds, masks).item())
            iou_sum += float(iou_score(preds, masks).item())
            n += 1

    result = EvalResult(
        run_dir=run_dir,
        loss=loss_sum / max(n, 1),
        dice=dice_sum / max(n, 1),
        iou=iou_sum / max(n, 1),
        n_samples=n,
    )
    eval_meta = {
        "loss": result.loss,
        "dice": result.dice,
        "iou": result.iou,
        "n_samples": result.n_samples,
        "datasetDir": str(dataset_dir),
        "runDir": str(run_dir),
    }
    (run_dir / "eval.json").write_text(json.dumps(eval_meta, indent=2), encoding="utf-8")
    return result
