from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from mcs_trainer.dataset.raw_zip import import_raw_zip
from mcs_trainer.dataset.schemas import RAW_SCHEMA_VERSION

from conftest import build_raw_zip, make_image_bytes


def test_import_valid_raw_zip(tmp_path: Path, tmp_cwd: Path) -> None:
    zip_path = tmp_path / "raw.zip"
    build_raw_zip(
        zip_path,
        samples=[
            {
                "meta": {
                    "id": "s1",
                    "image": "images/sample-1.jpg",
                    "width": 50,
                    "height": 50,
                    "contentType": "image/jpeg",
                },
                "data": make_image_bytes(50, 50, "RGB", "JPEG", (255, 0, 0)),
            },
            {
                "meta": {
                    "id": "s2",
                    "image": "images/sample-2.png",
                    "width": 50,
                    "height": 50,
                    "contentType": "image/png",
                },
                "data": make_image_bytes(50, 50, "RGB", "PNG", (0, 255, 0)),
            },
        ],
        dataset_id="ds-test",
    )

    dest = tmp_path / "dest"
    result = import_raw_zip(zip_path, dest)

    assert result.dataset_id == "ds-test"
    assert result.dataset_dir == dest / "ds-test"
    assert result.dataset_dir.exists()
    assert (result.dataset_dir / "metadata.json").exists()
    assert result.image_count == 2
    assert result.warnings == []

    meta = json.loads((result.dataset_dir / "metadata.json").read_text("utf-8"))
    assert len(meta["samples"]) == 2
    assert {s["id"] for s in meta["samples"]} == {"s1", "s2"}


def test_import_missing_metadata_json(tmp_path: Path) -> None:
    zip_path = tmp_path / "raw.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("images/sample-1.png", make_image_bytes(10, 10, "RGB", "PNG"))

    with pytest.raises(ValueError, match="metadata.json"):
        import_raw_zip(zip_path, tmp_path / "dest")


def test_import_wrong_schema_version(tmp_path: Path) -> None:
    zip_path = tmp_path / "raw.zip"
    build_raw_zip(
        zip_path,
        samples=[
            {
                "meta": {"id": "s1", "image": "images/sample-1.png"},
                "data": make_image_bytes(10, 10, "RGB", "PNG"),
            }
        ],
        schema_version="wrong",
    )

    with pytest.raises(ValueError, match="schemaVersion"):
        import_raw_zip(zip_path, tmp_path / "dest")


def test_import_missing_referenced_image(tmp_path: Path) -> None:
    zip_path = tmp_path / "raw.zip"
    build_raw_zip(
        zip_path,
        samples=[
            {
                "meta": {"id": "s1", "image": "images/sample-9999.jpg"},
                "data": None,
            }
        ],
    )

    with pytest.raises(FileNotFoundError, match="sample-9999"):
        import_raw_zip(zip_path, tmp_path / "dest")


def test_import_zip_slip_blocked(tmp_path: Path, tmp_cwd: Path) -> None:
    zip_path = tmp_path / "raw.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        meta = {
            "schemaVersion": RAW_SCHEMA_VERSION,
            "datasetId": "ds-slip",
            "exportedAt": "2024-01-01T00:00:00+00:00",
            "samples": [
                {"id": "s1", "image": ".."},
            ],
        }
        zf.writestr("metadata.json", json.dumps(meta))

    with pytest.raises(ValueError, match="Unsafe"):
        import_raw_zip(zip_path, tmp_path / "dest")

    assert not (tmp_cwd / "evil.png").exists()
    assert not (tmp_path / "evil.png").exists()


def test_import_dimension_mismatch_warning(tmp_path: Path) -> None:
    zip_path = tmp_path / "raw.zip"
    build_raw_zip(
        zip_path,
        samples=[
            {
                "meta": {
                    "id": "s1",
                    "image": "images/sample-1.png",
                    "width": 100,
                    "height": 100,
                    "contentType": "image/png",
                },
                "data": make_image_bytes(50, 50, "RGB", "PNG", (0, 0, 255)),
            }
        ],
    )

    result = import_raw_zip(zip_path, tmp_path / "dest")
    assert result.image_count == 1
    assert any("Mismatch" in w or "mismatch" in w for w in result.warnings)


def test_import_images_land_in_dataset_dir(tmp_path: Path) -> None:
    zip_path = tmp_path / "raw.zip"
    build_raw_zip(
        zip_path,
        samples=[
            {
                "meta": {
                    "id": "s1",
                    "image": "images/sample-1.png",
                    "width": 50,
                    "height": 50,
                    "contentType": "image/png",
                },
                "data": make_image_bytes(50, 50, "RGB", "PNG", (0, 0, 255)),
            }
        ],
        dataset_id="ds-x",
    )

    dest = tmp_path / "dest"
    result = import_raw_zip(zip_path, dest)
    assert (result.dataset_dir / "images" / "sample-1.png").exists()
