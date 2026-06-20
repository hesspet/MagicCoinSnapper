from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

from mcs_trainer.dataset.annotated_dataset import load_annotated


@dataclass
class SplitResult:
    train: list[str] = field(default_factory=list)
    val: list[str] = field(default_factory=list)
    test: list[str] = field(default_factory=list)

    @property
    def train_count(self) -> int:
        return len(self.train)

    @property
    def val_count(self) -> int:
        return len(self.val)

    @property
    def test_count(self) -> int:
        return len(self.test)


def make_split(
    dataset_dir: Path,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> SplitResult:
    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-6:
        raise ValueError(
            f"Ratios müssen 1.0 ergeben: {train_ratio + val_ratio + test_ratio}"
        )
    if min(train_ratio, val_ratio, test_ratio) < 0:
        raise ValueError("Ratios dürfen nicht negativ sein")

    dataset_dir = Path(dataset_dir)
    metadata = load_annotated(dataset_dir)

    ids = [s.id for s in metadata.samples if not s.excluded]
    rng = random.Random(seed)
    rng.shuffle(ids)

    n = len(ids)
    n_train = int(round(n * train_ratio))
    n_val = int(round(n * val_ratio))
    n_test = n - n_train - n_val
    if n_test < 0:
        n_test = 0

    train_ids = ids[:n_train]
    val_ids = ids[n_train : n_train + n_val]
    test_ids = ids[n_train + n_val : n_train + n_val + n_test]

    splits_dir = dataset_dir / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)
    (splits_dir / "train.txt").write_text(
        "\n".join(train_ids) + ("\n" if train_ids else ""), encoding="utf-8"
    )
    (splits_dir / "val.txt").write_text(
        "\n".join(val_ids) + ("\n" if val_ids else ""), encoding="utf-8"
    )
    (splits_dir / "test.txt").write_text(
        "\n".join(test_ids) + ("\n" if test_ids else ""), encoding="utf-8"
    )

    return SplitResult(train=train_ids, val=val_ids, test=test_ids)
