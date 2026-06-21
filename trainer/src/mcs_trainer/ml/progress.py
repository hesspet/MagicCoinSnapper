from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class TrainProgress:
    epoch: int
    total: int
    percent: float
    train_loss: float
    val_loss: float
    val_dice: float
    val_iou: float
    elapsed_s: float
    eta_s: float


def _format_float(value: float) -> str:
    if math.isnan(value):
        return "nan"
    return f"{value:.6f}"


def format_train_progress(
    *,
    epoch: int,
    total: int,
    train_loss: float,
    val_loss: float,
    val_dice: float,
    val_iou: float,
    elapsed_s: float,
    eta_s: float,
) -> str:
    percent = (epoch / max(total, 1)) * 100.0
    return (
        "TRAIN_PROGRESS "
        f"epoch={epoch} "
        f"total={total} "
        f"percent={percent:.1f} "
        f"train_loss={_format_float(train_loss)} "
        f"val_loss={_format_float(val_loss)} "
        f"val_dice={_format_float(val_dice)} "
        f"val_iou={_format_float(val_iou)} "
        f"elapsed_s={elapsed_s:.1f} "
        f"eta_s={eta_s:.1f}"
    )


def parse_train_progress(line: str) -> TrainProgress | None:
    line = line.strip()
    if not line.startswith("TRAIN_PROGRESS "):
        return None
    values: dict[str, str] = {}
    for part in line.split()[1:]:
        if "=" not in part:
            return None
        key, value = part.split("=", 1)
        values[key] = value
    try:
        return TrainProgress(
            epoch=int(values["epoch"]),
            total=int(values["total"]),
            percent=float(values["percent"]),
            train_loss=float(values["train_loss"]),
            val_loss=float(values["val_loss"]),
            val_dice=float(values["val_dice"]),
            val_iou=float(values["val_iou"]),
            elapsed_s=float(values["elapsed_s"]),
            eta_s=float(values["eta_s"]),
        )
    except (KeyError, ValueError):
        return None


def format_duration(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {sec:02d}s"
    return f"{sec}s"
