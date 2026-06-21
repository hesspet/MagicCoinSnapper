from __future__ import annotations

import math

from mcs_trainer.ml.progress import (
    format_duration,
    format_train_progress,
    parse_train_progress,
)


def test_format_and_parse_train_progress() -> None:
    line = format_train_progress(
        epoch=2,
        total=10,
        train_loss=0.1234567,
        val_loss=math.nan,
        val_dice=0.5,
        val_iou=0.25,
        elapsed_s=12.34,
        eta_s=49.87,
    )

    progress = parse_train_progress(line)

    assert line.startswith("TRAIN_PROGRESS ")
    assert progress is not None
    assert progress.epoch == 2
    assert progress.total == 10
    assert progress.percent == 20.0
    assert progress.train_loss == 0.123457
    assert math.isnan(progress.val_loss)
    assert progress.val_dice == 0.5
    assert progress.val_iou == 0.25
    assert progress.elapsed_s == 12.3
    assert progress.eta_s == 49.9


def test_parse_train_progress_ignores_other_lines() -> None:
    assert parse_train_progress("hello") is None
    assert parse_train_progress("TRAIN_PROGRESS epoch=nope") is None


def test_format_duration() -> None:
    assert format_duration(4.2) == "4s"
    assert format_duration(65) == "1m 05s"
    assert format_duration(3720) == "1h 02m"
