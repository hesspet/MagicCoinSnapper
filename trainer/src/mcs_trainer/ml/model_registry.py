from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcs_trainer import __version__
from mcs_trainer.utils.paths import slugify_dataset_id


MODEL_INDEX_SCHEMA_VERSION = "mcs-model-index-v1"
MODEL_CONTRACT = "mcs-segmentation-512-v1"
MODEL_FILENAME = "coin-segmentation.onnx"
MODEL_METADATA_FILENAME = "model.json"


DEFAULT_INPUT_CONTRACT = {
    "name": "input",
    "dtype": "float32",
    "shape": [1, 3, 512, 512],
    "layout": "NCHW",
    "colorOrder": "RGB",
    "normalization": "/255",
    "range": [0.0, 1.0],
}
DEFAULT_OUTPUT_CONTRACT = {
    "name": "mask",
    "dtype": "float32",
    "shape": [1, 1, 512, 512],
    "range": [0.0, 1.0],
    "threshold": 0.5,
}


@dataclass
class InstallResult:
    model_id: str
    model_dir: Path
    manifest_path: Path
    backups: list[Path] = field(default_factory=list)


def build_model_metadata(
    *,
    model_id: str,
    display_name: str,
    description: str = "",
    object_type: str = "coin",
    currency: str = "unknown",
    use_case: str = "segmentation",
    profile: str = "general",
    version: str = __version__,
    model_url: str | None = None,
    metadata_url: str | None = None,
    created_at: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    safe_id = slugify_dataset_id(model_id)
    metadata = {
        "id": safe_id,
        "displayName": display_name.strip() or safe_id,
        "description": description.strip(),
        "objectType": object_type.strip() or "coin",
        "currency": currency.strip() or "unknown",
        "useCase": use_case.strip() or "segmentation",
        "profile": profile.strip() or "general",
        "version": version.strip() or __version__,
        "modelUrl": model_url or f"models/{safe_id}/{MODEL_FILENAME}",
        "metadataUrl": metadata_url or f"models/{safe_id}/{MODEL_METADATA_FILENAME}",
        "contract": MODEL_CONTRACT,
        "input": dict(DEFAULT_INPUT_CONTRACT),
        "output": dict(DEFAULT_OUTPUT_CONTRACT),
        "createdAt": created_at or datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        metadata.update(extra)
        metadata["id"] = slugify_dataset_id(str(metadata.get("id", safe_id)))
        metadata.setdefault("contract", MODEL_CONTRACT)
        metadata.setdefault("input", dict(DEFAULT_INPUT_CONTRACT))
        metadata.setdefault("output", dict(DEFAULT_OUTPUT_CONTRACT))
        metadata.setdefault("modelUrl", f"models/{metadata['id']}/{MODEL_FILENAME}")
        metadata.setdefault("metadataUrl", f"models/{metadata['id']}/{MODEL_METADATA_FILENAME}")
    return metadata


def normalize_model_metadata(metadata: dict[str, Any], *, profile: str = "general") -> dict[str, Any]:
    model_id = str(metadata.get("id") or f"coin-segmentation-{profile}")
    return build_model_metadata(
        model_id=model_id,
        display_name=str(metadata.get("displayName") or model_id),
        description=str(metadata.get("description") or ""),
        object_type=str(metadata.get("objectType") or "coin"),
        currency=str(metadata.get("currency") or "unknown"),
        use_case=str(metadata.get("useCase") or "segmentation"),
        profile=str(metadata.get("profile") or profile),
        version=str(metadata.get("version") or __version__),
        model_url=metadata.get("modelUrl"),
        metadata_url=metadata.get("metadataUrl"),
        created_at=metadata.get("createdAt"),
        extra=metadata,
    )


def model_install_targets_exist(pwa_wwwroot: Path, model_id: str) -> bool:
    models_root = Path(pwa_wwwroot) / "models"
    safe_id = slugify_dataset_id(model_id)
    return (models_root / safe_id).exists() or (models_root / MODEL_FILENAME).exists()


def install_model_into_pwa(
    *,
    onnx_path: Path,
    pwa_wwwroot: Path,
    metadata: dict[str, Any],
    backup_existing: bool = True,
    make_default: bool = True,
) -> InstallResult:
    onnx_path = Path(onnx_path).resolve()
    if not onnx_path.exists():
        raise FileNotFoundError(f"ONNX-Datei nicht gefunden: {onnx_path}")

    model_meta = normalize_model_metadata(metadata)
    model_id = str(model_meta["id"])
    model_meta["modelUrl"] = f"models/{model_id}/{MODEL_FILENAME}"
    model_meta["metadataUrl"] = f"models/{model_id}/{MODEL_METADATA_FILENAME}"

    models_root = Path(pwa_wwwroot) / "models"
    models_root.mkdir(parents=True, exist_ok=True)
    target_dir = models_root / model_id
    backups: list[Path] = []

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    legacy_onnx = models_root / MODEL_FILENAME
    if legacy_onnx.exists():
        if not backup_existing:
            raise FileExistsError(f"Legacy-ONNX existiert bereits: {legacy_onnx}")
        backup_path = models_root / f"{MODEL_FILENAME}.backup-{timestamp}"
        suffix = 1
        while backup_path.exists():
            backup_path = models_root / f"{MODEL_FILENAME}.backup-{timestamp}-{suffix}"
            suffix += 1
        shutil.move(str(legacy_onnx), str(backup_path))
        backups.append(backup_path)

    if target_dir.exists():
        if not backup_existing:
            raise FileExistsError(f"Modell existiert bereits: {target_dir}")
        backup_dir = models_root / f"{model_id}.backup-{timestamp}"
        suffix = 1
        while backup_dir.exists():
            backup_dir = models_root / f"{model_id}.backup-{timestamp}-{suffix}"
            suffix += 1
        shutil.move(str(target_dir), str(backup_dir))
        backups.append(backup_dir)

    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(onnx_path, target_dir / MODEL_FILENAME)
    (target_dir / MODEL_METADATA_FILENAME).write_text(
        json.dumps(model_meta, indent=2), encoding="utf-8"
    )

    manifest_path = models_root / "manifest.json"
    manifest = _load_manifest(manifest_path)
    entries = [m for m in manifest.get("models", []) if m.get("id") != model_id]
    entries.append(_manifest_entry(model_meta))
    manifest["schemaVersion"] = MODEL_INDEX_SCHEMA_VERSION
    manifest["defaultModelId"] = model_id if make_default else manifest.get("defaultModelId", model_id)
    manifest["models"] = entries
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return InstallResult(
        model_id=model_id,
        model_dir=target_dir,
        manifest_path=manifest_path,
        backups=backups,
    )


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schemaVersion": MODEL_INDEX_SCHEMA_VERSION,
            "defaultModelId": None,
            "models": [],
        }
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    raw.setdefault("models", [])
    if not isinstance(raw["models"], list):
        raw["models"] = []
    return raw


def _manifest_entry(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": metadata["id"],
        "displayName": metadata["displayName"],
        "description": metadata.get("description", ""),
        "objectType": metadata.get("objectType", "coin"),
        "currency": metadata.get("currency", "unknown"),
        "useCase": metadata.get("useCase", "segmentation"),
        "profile": metadata.get("profile", "general"),
        "version": metadata.get("version", __version__),
        "modelUrl": metadata["modelUrl"],
        "metadataUrl": metadata["metadataUrl"],
        "contract": metadata.get("contract", MODEL_CONTRACT),
        "input": metadata.get("input", DEFAULT_INPUT_CONTRACT),
        "output": metadata.get("output", DEFAULT_OUTPUT_CONTRACT),
    }
