from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mcs_trainer.dataset.schemas import (
    ANNOTATED_SCHEMA_VERSION,
    AnnotatedMetadata,
)
from mcs_trainer.utils.paths import ensure_subdirs, slugify_dataset_id


def load_annotated(dataset_dir: Path) -> AnnotatedMetadata:
    dataset_dir = Path(dataset_dir)
    meta_path = dataset_dir / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json fehlt: {meta_path}")
    raw = json.loads(meta_path.read_text(encoding="utf-8"))
    return AnnotatedMetadata.model_validate(raw)


def save_annotated(metadata: AnnotatedMetadata, dataset_dir: Path) -> None:
    dataset_dir = Path(dataset_dir)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    meta_path = dataset_dir / "metadata.json"
    meta_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")


def create_annotated_skeleton(
    root: Path, dataset_id: str, source: str | None = None
) -> Path:
    slug = slugify_dataset_id(dataset_id)
    dataset_dir = Path(root) / slug
    ensure_subdirs(dataset_dir, ["images", "masks", "splits"])
    metadata = AnnotatedMetadata(
        schemaVersion=ANNOTATED_SCHEMA_VERSION,
        datasetId=slug,
        createdAt=datetime.now(timezone.utc),
        source=source,
        samples=[],
    )
    save_annotated(metadata, dataset_dir)
    return dataset_dir
