from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from mcs_trainer.dataset.schemas import (
    RAW_SCHEMA_VERSION,
    RawMetadata,
    RawSample,
)
from mcs_trainer.utils.paths import ensure_subdirs, safe_join


@dataclass
class RawImportResult:
    dataset_id: str
    dataset_dir: Path
    image_count: int
    warnings: list[str] = field(default_factory=list)


_CONTENT_TYPE_MAP = {
    "image/jpeg": ("JPEG", ".jpg"),
    "image/png": ("PNG", ".png"),
}


def import_raw_zip(zip_path: Path, dest_root: Path) -> RawImportResult:
    zip_path = Path(zip_path)
    dest_root = Path(dest_root)
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP nicht gefunden: {zip_path}")

    warnings: list[str] = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        metadata_name = next(
            (n for n in names if n.rstrip("/") == "metadata.json"), None
        )
        if metadata_name is None:
            raise ValueError("metadata.json fehlt im ZIP")
        with zf.open(metadata_name) as fh:
            raw_json = json.loads(fh.read().decode("utf-8"))

        try:
            metadata = RawMetadata.model_validate(raw_json)
        except Exception as exc:
            raise ValueError(f"Ungültige metadata.json: {exc}") from exc

        if metadata.schemaVersion != RAW_SCHEMA_VERSION:
            raise ValueError(
                f"schemaVersion '{metadata.schemaVersion}' nicht unterstützt "
                f"(erwartet '{RAW_SCHEMA_VERSION}')"
            )

        dataset_dir = dest_root / metadata.datasetId
        dirs = ensure_subdirs(dataset_dir, ["images"])

        seen_ids: set[str] = set()
        kept_samples: list[RawSample] = []

        for sample in metadata.samples:
            if sample.id in seen_ids:
                warnings.append(f"Doppelte Sample-ID ignoriert: {sample.id}")
                continue
            seen_ids.add(sample.id)

            rel_image = sample.image.replace("\\", "/")
            basename = rel_image.split("/", 1)[-1]
            if not basename or basename in (".", "..") or "/" in basename or "\\" in basename:
                raise ValueError(
                    f"Unsafe Bildpfad '{sample.image}' (Sample {sample.id})"
                )
            target_path = safe_join(dataset_dir, f"images/{basename}")

            try:
                src_info = zf.getinfo(rel_image)
            except KeyError:
                raise FileNotFoundError(
                    f"Bild im ZIP fehlt: {rel_image} (Sample {sample.id})"
                )

            with zf.open(src_info) as src_fh:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, "wb") as out_fh:
                    shutil.copyfileobj(src_fh, out_fh)

            try:
                with Image.open(target_path) as img:
                    img.verify()
                with Image.open(target_path) as img:
                    actual_w, actual_h = img.size
                    actual_format = img.format
            except Exception as exc:
                warnings.append(f"Bild nicht lesbar ({sample.id}): {exc}")
                kept_samples.append(sample)
                continue

            if sample.width is not None and sample.width != actual_w:
                warnings.append(
                    f"Breiten-Mismatch ({sample.id}): "
                    f"metadata={sample.width}, bild={actual_w}"
                )
            if sample.height is not None and sample.height != actual_h:
                warnings.append(
                    f"Höhen-Mismatch ({sample.id}): "
                    f"metadata={sample.height}, bild={actual_h}"
                )
            if sample.contentType is not None:
                expected_fmt, _ = _CONTENT_TYPE_MAP.get(
                    sample.contentType, (None, None)
                )
                if expected_fmt is not None and actual_format != expected_fmt:
                    warnings.append(
                        f"ContentType-Mismatch ({sample.id}): "
                        f"metadata={sample.contentType}, bild={actual_format}"
                    )

            if sample.sizeBytes is not None and sample.sizeBytes != src_info.file_size:
                warnings.append(
                    f"sizeBytes-Mismatch ({sample.id}): "
                    f"metadata={sample.sizeBytes}, datei={src_info.file_size}"
                )

            kept_samples.append(sample)

        normalized = metadata.model_copy(update={"samples": kept_samples})
        metadata_path = dataset_dir / "metadata.json"
        metadata_path.write_text(
            normalized.model_dump_json(indent=2), encoding="utf-8"
        )

    return RawImportResult(
        dataset_id=metadata.datasetId,
        dataset_dir=dataset_dir,
        image_count=len(kept_samples),
        warnings=warnings,
    )
