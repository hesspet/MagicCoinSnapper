from __future__ import annotations

from pathlib import Path

from mcs_trainer.dataset.splits import make_split

from conftest import build_annotated_dataset


def _build_n_samples(root: Path, dataset_id: str, n: int, excluded_ids: set[str] | None = None) -> Path:
    excluded_ids = excluded_ids or set()
    specs = [
        {"id": f"s{i}", "width": 16, "height": 16, "excluded": f"s{i}" in excluded_ids}
        for i in range(n)
    ]
    return build_annotated_dataset(root, dataset_id, specs)


def test_split_ratios(tmp_path: Path) -> None:
    ds = _build_n_samples(tmp_path, "ds-split", 10)

    result = make_split(ds, 0.8, 0.1, 0.1, seed=42)

    assert result.train_count + result.val_count + result.test_count == 10
    assert len(result.train) == 8
    assert len(result.val) == 1
    assert len(result.test) == 1


def test_split_excluded_excluded(tmp_path: Path) -> None:
    ds = _build_n_samples(tmp_path, "ds-excl", 6, excluded_ids={"s3", "s5"})

    result = make_split(ds, 0.8, 0.1, 0.1, seed=7)

    all_ids = result.train + result.val + result.test
    assert "s3" not in all_ids
    assert "s5" not in all_ids
    assert len(all_ids) == 4


def test_split_deterministic(tmp_path: Path) -> None:
    ds = _build_n_samples(tmp_path, "ds-det", 8)
    make_split(ds, 0.75, 0.125, 0.125, seed=42)

    train_a = (ds / "splits" / "train.txt").read_text("utf-8")
    val_a = (ds / "splits" / "val.txt").read_text("utf-8")
    test_a = (ds / "splits" / "test.txt").read_text("utf-8")

    import shutil
    ds2 = shutil.copytree(ds, tmp_path / "ds-det-2")
    make_split(ds2, 0.75, 0.125, 0.125, seed=42)

    assert (ds2 / "splits" / "train.txt").read_text("utf-8") == train_a
    assert (ds2 / "splits" / "val.txt").read_text("utf-8") == val_a
    assert (ds2 / "splits" / "test.txt").read_text("utf-8") == test_a


def test_split_no_overlap(tmp_path: Path) -> None:
    ds = _build_n_samples(tmp_path, "ds-nov", 12)
    result = make_split(ds, 0.7, 0.15, 0.15, seed=3)

    train, val, test = set(result.train), set(result.val), set(result.test)
    assert not (train & val)
    assert not (train & test)
    assert not (val & test)
    assert train | val | test == {f"s{i}" for i in range(12)}
