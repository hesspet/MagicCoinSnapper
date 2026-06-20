from __future__ import annotations

from pathlib import Path

from mcs_trainer.dataset.validation import validate_annotated

from conftest import build_annotated_dataset, make_image_bytes, make_mask_bytes, write_split_file


def test_validate_annotated_ok(tmp_path: Path) -> None:
    ds = build_annotated_dataset(
        tmp_path,
        "ds-ann-ok",
        [
            {"id": "s1", "width": 32, "height": 24},
            {"id": "s2", "width": 32, "height": 24, "excluded": False},
        ],
    )

    result = validate_annotated(ds)
    assert result.ok
    assert result.errors == []


def test_validate_annotated_mask_wrong_dims(tmp_path: Path) -> None:
    ds = build_annotated_dataset(
        tmp_path,
        "ds-ann-wdim",
        [
            {
                "id": "s1",
                "width": 32,
                "height": 24,
                "mask_bytes": make_mask_bytes(20, 16, "L", 0),
            }
        ],
    )

    result = validate_annotated(ds)
    assert not result.ok
    assert any("Dimensionen" in e or "maske" in e.lower() for e in result.errors)


def test_validate_annotated_mask_non_binary_values(tmp_path: Path) -> None:
    ds = build_annotated_dataset(
        tmp_path,
        "ds-ann-nb",
        [
            {
                "id": "s1",
                "width": 16,
                "height": 16,
                "mask_bytes": make_mask_bytes(16, 16, "L", 128),
            }
        ],
    )

    result = validate_annotated(ds)
    assert not result.ok
    assert any("0-255" in e or "{0,255}" in e for e in result.errors)


def test_validate_annotated_mask_not_grayscale(tmp_path: Path) -> None:
    ds = build_annotated_dataset(
        tmp_path,
        "ds-ann-rgb",
        [
            {
                "id": "s1",
                "width": 16,
                "height": 16,
                "mask_bytes": make_mask_bytes(16, 16, "RGB", (0, 0, 0)),
            }
        ],
    )

    result = validate_annotated(ds)
    assert not result.ok
    assert any("Graustufen" in e or "mode=" in e for e in result.errors)


def test_validate_annotated_excluded_in_split(tmp_path: Path) -> None:
    ds = build_annotated_dataset(
        tmp_path,
        "ds-ann-excl",
        [
            {"id": "s1", "width": 16, "height": 16, "excluded": False},
            {"id": "s2", "width": 16, "height": 16, "excluded": True},
        ],
    )
    write_split_file(ds, "train", ["s1", "s2"])
    write_split_file(ds, "val", [])
    write_split_file(ds, "test", [])

    result = validate_annotated(ds)
    assert not result.ok
    assert any("Excluded" in e and "s2" in e for e in result.errors)


def test_validate_annotated_missing_mask(tmp_path: Path) -> None:
    ds = build_annotated_dataset(
        tmp_path,
        "ds-ann-nomask",
        [
            {
                "id": "s1",
                "width": 16,
                "height": 16,
                "write_mask": False,
            }
        ],
    )

    result = validate_annotated(ds)
    assert not result.ok
    assert any("Maske fehlt" in e for e in result.errors)


def test_validate_annotated_split_id_mismatch(tmp_path: Path) -> None:
    ds = build_annotated_dataset(
        tmp_path,
        "ds-ann-splitid",
        [
            {"id": "s1", "width": 16, "height": 16},
        ],
    )
    write_split_file(ds, "train", ["s1", "ghost-id"])
    write_split_file(ds, "val", [])
    write_split_file(ds, "test", [])

    result = validate_annotated(ds)
    assert not result.ok
    assert any("unbekannte ID" in e and "ghost-id" in e for e in result.errors)
