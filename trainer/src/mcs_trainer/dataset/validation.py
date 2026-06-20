from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from mcs_trainer.dataset.schemas import (
    ANNOTATED_SCHEMA_VERSION,
    RAW_SCHEMA_VERSION,
    AnnotatedMetadata,
    RawMetadata,
)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _read_metadata(dataset_dir: Path) -> dict:
    meta_path = dataset_dir / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json fehlt: {meta_path}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def validate_raw(dataset_dir: Path) -> ValidationResult:
    result = ValidationResult()
    dataset_dir = Path(dataset_dir)

    try:
        raw = _read_metadata(dataset_dir)
    except FileNotFoundError as exc:
        result.errors.append(str(exc))
        return result
    except Exception as exc:
        result.errors.append(f"metadata.json ungültig: {exc}")
        return result

    try:
        metadata = RawMetadata.model_validate(raw)
    except Exception as exc:
        result.errors.append(f"metadata.json Schema-Fehler: {exc}")
        return result

    if metadata.schemaVersion != RAW_SCHEMA_VERSION:
        result.errors.append(
            f"schemaVersion falsch: '{metadata.schemaVersion}' "
            f"(erwartet '{RAW_SCHEMA_VERSION}')"
        )

    for sample in metadata.samples:
        img_path = dataset_dir / sample.image
        if not img_path.exists():
            result.errors.append(f"Bild fehlt ({sample.id}): {sample.image}")
            continue
        try:
            with Image.open(img_path) as img:
                img.verify()
            with Image.open(img_path) as img:
                w, h = img.size
        except Exception as exc:
            result.errors.append(f"Bild nicht lesbar ({sample.id}): {exc}")
            continue
        if sample.width is not None and sample.width != w:
            result.warnings.append(
                f"Breiten-Mismatch ({sample.id}): metadata={sample.width}, bild={w}"
            )
        if sample.height is not None and sample.height != h:
            result.warnings.append(
                f"Höhen-Mismatch ({sample.id}): metadata={sample.height}, bild={h}"
            )

    return result


def validate_annotated(dataset_dir: Path) -> ValidationResult:
    result = ValidationResult()
    dataset_dir = Path(dataset_dir)

    try:
        raw = _read_metadata(dataset_dir)
    except FileNotFoundError as exc:
        result.errors.append(str(exc))
        return result
    except Exception as exc:
        result.errors.append(f"metadata.json ungültig: {exc}")
        return result

    try:
        metadata = AnnotatedMetadata.model_validate(raw)
    except Exception as exc:
        result.errors.append(f"metadata.json Schema-Fehler: {exc}")
        return result

    if metadata.schemaVersion != ANNOTATED_SCHEMA_VERSION:
        result.errors.append(
            f"schemaVersion falsch: '{metadata.schemaVersion}' "
            f"(erwartet '{ANNOTATED_SCHEMA_VERSION}')"
        )

    splits_dir = dataset_dir / "splits"
    split_ids: dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
    for name in ("train", "val", "test"):
        split_path = splits_dir / f"{name}.txt"
        if not split_path.exists():
            result.warnings.append(f"Split-Datei fehlt: splits/{name}.txt")
            continue
        for line in split_path.read_text(encoding="utf-8").splitlines():
            sid = line.strip()
            if sid:
                split_ids[name].add(sid)

    sample_ids = {s.id for s in metadata.samples}

    for sname, sids in split_ids.items():
        for sid in sids:
            if sid not in sample_ids:
                result.errors.append(
                    f"Split {sname} enthält unbekannte ID: {sid}"
                )

    excluded_ids = {s.id for s in metadata.samples if s.excluded}
    for sname, sids in split_ids.items():
        overlap = excluded_ids & sids
        for sid in overlap:
            result.errors.append(
                f"Excluded Sample in Split {sname}: {sid}"
            )

    for sample in metadata.samples:
        img_path = dataset_dir / sample.image
        if not img_path.exists():
            result.errors.append(f"Bild fehlt ({sample.id}): {sample.image}")
        mask_path = dataset_dir / sample.mask
        if not mask_path.exists():
            result.errors.append(f"Maske fehlt ({sample.id}): {sample.mask}")
            continue
        if img_path.exists():
            try:
                with Image.open(img_path) as img:
                    img.verify()
                with Image.open(img_path) as img:
                    iw, ih = img.size
            except Exception as exc:
                result.errors.append(f"Bild nicht lesbar ({sample.id}): {exc}")
                iw = ih = None
        else:
            iw = ih = None
        try:
            with Image.open(mask_path) as mask:
                mask.verify()
            with Image.open(mask_path) as mask:
                if mask.format != "PNG":
                    result.errors.append(
                        f"Maske kein PNG ({sample.id}): {mask.format}"
                    )
                if mask.mode != "L":
                    result.errors.append(
                        f"Maske nicht 8-bit Graustufen ({sample.id}): mode={mask.mode}"
                    )
                mw, mh = mask.size
                if mask.mode == "L":
                    extrema = mask.getextrema()
                    if extrema[0] < 0 or extrema[1] > 255:
                        result.errors.append(
                            f"Maskenwerte ausserhalb 0-255 ({sample.id}): {extrema}"
                        )
                    elif extrema[1] > 0 and (
                        extrema[0] not in (0, 255) or extrema[1] not in (0, 255)
                    ):
                        result.errors.append(
                            f"Maskenwerte nicht in {{0,255}} ({sample.id}): {extrema}"
                        )
        except Exception as exc:
            result.errors.append(f"Maske nicht lesbar ({sample.id}): {exc}")
            continue
        if iw is not None and (mw != iw or mh != ih):
            result.errors.append(
                f"Masken-Dimensionen != Bild ({sample.id}): "
                f"bild={iw}x{ih}, maske={mw}x{mh}"
            )
        if sample.width != mw or sample.height != mh:
            result.warnings.append(
                f"Metadata-Dimensionen != Maske ({sample.id}): "
                f"metadata={sample.width}x{sample.height}, maske={mw}x{mh}"
            )

    return result
