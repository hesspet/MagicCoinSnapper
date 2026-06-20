from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

import pytest
from PIL import Image

from mcs_trainer.dataset.schemas import (
    ANNOTATED_SCHEMA_VERSION,
    RAW_SCHEMA_VERSION,
)


@pytest.fixture(autouse=True)
def tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def make_image_bytes(
    width: int,
    height: int,
    mode: str = "RGB",
    format: str = "PNG",
    color: Any = (255, 0, 0),
) -> bytes:
    buf = io.BytesIO()
    Image.new(mode, (width, height), color).save(buf, format)
    return buf.getvalue()


def make_mask_bytes(
    width: int,
    height: int,
    mode: str = "L",
    color: Any = 0,
) -> bytes:
    buf = io.BytesIO()
    img = Image.new(mode, (width, height), color)
    if mode == "L":
        for x in range(min(width, 4)):
            for y in range(min(height, 4)):
                img.putpixel((x, y), 255)
    img.save(buf, "PNG")
    return buf.getvalue()


def build_raw_zip(
    zip_path: Path,
    samples: list[dict[str, Any]],
    dataset_id: str = "ds-test",
    schema_version: str = RAW_SCHEMA_VERSION,
    exported_at: str = "2024-01-01T00:00:00+00:00",
    source: Optional[str] = None,
    extra_meta: Optional[dict[str, Any]] = None,
) -> Path:
    meta: dict[str, Any] = {
        "schemaVersion": schema_version,
        "datasetId": dataset_id,
        "exportedAt": exported_at,
        "source": source,
        "samples": [s["meta"] for s in samples],
    }
    if extra_meta:
        meta.update(extra_meta)

    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("metadata.json", json.dumps(meta))
        for s in samples:
            data = s.get("data")
            if data is not None:
                name = s["meta"]["image"]
                zf.writestr(name, data)
    return zip_path


def build_annotated_dataset(
    root: Path,
    dataset_id: str,
    sample_specs: list[dict[str, Any]],
    schema_version: str = ANNOTATED_SCHEMA_VERSION,
    source: Optional[str] = None,
) -> Path:
    root = Path(root)
    dataset_dir = root / dataset_id
    (dataset_dir / "images").mkdir(parents=True, exist_ok=True)
    (dataset_dir / "masks").mkdir(parents=True, exist_ok=True)
    (dataset_dir / "splits").mkdir(parents=True, exist_ok=True)

    samples_meta: list[dict[str, Any]] = []
    for spec in sample_specs:
        sid = spec["id"]
        width = spec["width"]
        height = spec["height"]
        image_name = spec.get("image_name", f"images/{sid}.png")
        mask_name = spec.get("mask_name", f"masks/{sid}.png")
        excluded = spec.get("excluded", False)

        image_bytes = spec.get("image_bytes")
        if image_bytes is None:
            image_bytes = make_image_bytes(width, height, "RGB", "PNG", (10, 20, 30))
        (dataset_dir / image_name).parent.mkdir(parents=True, exist_ok=True)
        if spec.get("write_image", True):
            (dataset_dir / image_name).write_bytes(image_bytes)

        mask_bytes = spec.get("mask_bytes")
        if mask_bytes is None:
            mask_bytes = make_mask_bytes(width, height, "L", 0)
        (dataset_dir / mask_name).parent.mkdir(parents=True, exist_ok=True)
        if spec.get("write_mask", True):
            (dataset_dir / mask_name).write_bytes(mask_bytes)

        samples_meta.append(
            {
                "id": sid,
                "image": image_name,
                "mask": mask_name,
                "width": width,
                "height": height,
                "contentType": spec.get("contentType", "image/png"),
                "excluded": excluded,
                "notes": spec.get("notes"),
                "tags": spec.get("tags", []),
            }
        )

    meta = {
        "schemaVersion": schema_version,
        "datasetId": dataset_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "samples": samples_meta,
    }
    (dataset_dir / "metadata.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    return dataset_dir


def write_split_file(dataset_dir: Path, name: str, ids: list[str]) -> None:
    splits_dir = dataset_dir / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)
    (splits_dir / f"{name}.txt").write_text(
        "\n".join(ids) + ("\n" if ids else ""), encoding="utf-8"
    )
