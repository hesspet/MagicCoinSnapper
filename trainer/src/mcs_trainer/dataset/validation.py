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


_MASK_ANALYSIS_MAX_SIDE = 512
_SMALL_MASK_COVERAGE = 0.002
_LARGE_MASK_COVERAGE = 0.9


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


def _analysis_mask(mask: Image.Image) -> Image.Image:
    w, h = mask.size
    scale = min(1.0, _MASK_ANALYSIS_MAX_SIDE / max(w, h))
    if scale < 1.0:
        size = (max(1, round(w * scale)), max(1, round(h * scale)))
        mask = mask.resize(size, Image.Resampling.NEAREST)
    return mask.point(lambda v: 255 if v >= 128 else 0).convert("L")


def _component_stats(mask: Image.Image, value: int) -> tuple[int, int, int]:
    w, h = mask.size
    data = bytes(mask.getdata())
    visited = bytearray(w * h)
    components = 0
    largest = 0
    enclosed = 0

    for start, pixel in enumerate(data):
        if visited[start] or pixel != value:
            continue
        components += 1
        size = 0
        touches_border = False
        stack = [start]
        visited[start] = 1
        while stack:
            idx = stack.pop()
            size += 1
            x = idx % w
            y = idx // w
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                touches_border = True
            if x > 0:
                nidx = idx - 1
                if not visited[nidx] and data[nidx] == value:
                    visited[nidx] = 1
                    stack.append(nidx)
            if x < w - 1:
                nidx = idx + 1
                if not visited[nidx] and data[nidx] == value:
                    visited[nidx] = 1
                    stack.append(nidx)
            if y > 0:
                nidx = idx - w
                if not visited[nidx] and data[nidx] == value:
                    visited[nidx] = 1
                    stack.append(nidx)
            if y < h - 1:
                nidx = idx + w
                if not visited[nidx] and data[nidx] == value:
                    visited[nidx] = 1
                    stack.append(nidx)
        largest = max(largest, size)
        if not touches_border:
            enclosed += 1

    return components, largest, enclosed


def _warn_mask_geometry(
    result: ValidationResult, sample_id: str, mask: Image.Image
) -> None:
    w, h = mask.size
    if (
        mask.crop((0, 0, w, 1)).getextrema()[1] > 0
        or mask.crop((0, h - 1, w, h)).getextrema()[1] > 0
        or mask.crop((0, 0, 1, h)).getextrema()[1] > 0
        or mask.crop((w - 1, 0, w, h)).getextrema()[1] > 0
    ):
        result.warnings.append(f"Maske berührt Bildrand ({sample_id})")

    analysis = _analysis_mask(mask)
    fg_components, largest_fg, _ = _component_stats(analysis, 255)
    fg_pixels = sum(1 for pixel in analysis.getdata() if pixel == 255)
    if fg_components > 4 or (
        fg_components > 1 and fg_pixels > 0 and largest_fg / fg_pixels < 0.95
    ):
        result.warnings.append(
            f"Maske wirkt fragmentiert ({sample_id}): komponenten={fg_components}"
        )

    _, _, holes = _component_stats(analysis, 0)
    if holes > 0:
        result.warnings.append(f"Maske enthält mögliche Löcher ({sample_id}): {holes}")


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
                    hist = mask.histogram()
                    mid_values = sum(hist[1:255])
                    fg_pixels = hist[255]
                    total_pixels = mw * mh
                    if mid_values:
                        result.errors.append(
                            f"Maskenwerte nicht in {{0,255}} ({sample.id})"
                        )
                    if fg_pixels == 0 and mid_values == 0:
                        result.errors.append(f"Maske leer ({sample.id})")
                    if fg_pixels > 0:
                        coverage = fg_pixels / total_pixels
                        if coverage < _SMALL_MASK_COVERAGE:
                            result.warnings.append(
                                f"Masken-Coverage sehr klein ({sample.id}): "
                                f"{coverage:.4%}"
                            )
                        if coverage > _LARGE_MASK_COVERAGE:
                            result.warnings.append(
                                f"Masken-Coverage sehr groß ({sample.id}): "
                                f"{coverage:.2%}"
                            )
                        _warn_mask_geometry(result, sample.id, mask)
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
