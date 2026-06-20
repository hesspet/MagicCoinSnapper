from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mcs_trainer.dataset.schemas import RAW_SCHEMA_VERSION
from mcs_trainer.dataset.validation import validate_raw

from conftest import make_image_bytes


def _write_raw_dataset(
    dataset_dir: Path,
    samples: list[dict],
    dataset_id: str = "ds-raw",
    schema_version: str = RAW_SCHEMA_VERSION,
) -> Path:
    dataset_dir = Path(dataset_dir)
    (dataset_dir / "images").mkdir(parents=True, exist_ok=True)
    meta = {
        "schemaVersion": schema_version,
        "datasetId": dataset_id,
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "source": None,
        "samples": [s["meta"] for s in samples],
    }
    for s in samples:
        data = s.get("data")
        if data is not None and s.get("write_image", True):
            p = dataset_dir / s["meta"]["image"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    (dataset_dir / "metadata.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    return dataset_dir


def test_validate_raw_ok(tmp_path: Path) -> None:
    ds = tmp_path / "ds-ok"
    _write_raw_dataset(
        ds,
        [
            {
                "meta": {
                    "id": "s1",
                    "image": "images/s1.png",
                    "width": 40,
                    "height": 30,
                    "contentType": "image/png",
                },
                "data": make_image_bytes(40, 30, "RGB", "PNG", (1, 2, 3)),
            }
        ],
    )

    result = validate_raw(ds)
    assert result.ok
    assert result.errors == []


def test_validate_raw_missing_image(tmp_path: Path) -> None:
    ds = tmp_path / "ds-missing"
    _write_raw_dataset(
        ds,
        [
            {
                "meta": {"id": "s1", "image": "images/s1.png"},
                "data": make_image_bytes(10, 10, "RGB", "PNG"),
                "write_image": False,
            }
        ],
    )

    result = validate_raw(ds)
    assert not result.ok
    assert any("fehlt" in e for e in result.errors)


def test_validate_raw_bad_schema_version(tmp_path: Path) -> None:
    ds = tmp_path / "ds-schema"
    _write_raw_dataset(
        ds,
        [
            {
                "meta": {"id": "s1", "image": "images/s1.png"},
                "data": make_image_bytes(10, 10, "RGB", "PNG"),
            }
        ],
        schema_version="nope",
    )

    result = validate_raw(ds)
    assert not result.ok
    assert any("schemaVersion" in e for e in result.errors)


def test_validate_raw_dimension_mismatch(tmp_path: Path) -> None:
    ds = tmp_path / "ds-dim"
    _write_raw_dataset(
        ds,
        [
            {
                "meta": {
                    "id": "s1",
                    "image": "images/s1.png",
                    "width": 100,
                    "height": 100,
                    "contentType": "image/png",
                },
                "data": make_image_bytes(50, 50, "RGB", "PNG", (5, 5, 5)),
            }
        ],
    )

    result = validate_raw(ds)
    assert result.ok
    assert result.errors == []
    assert len(result.warnings) >= 2
