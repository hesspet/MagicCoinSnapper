from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcs_trainer.ml.model_registry import (
    MODEL_INDEX_SCHEMA_VERSION,
    build_model_metadata,
    install_model_into_pwa,
)


def test_install_model_creates_manifest_and_model_files(tmp_path: Path) -> None:
    onnx = tmp_path / "model.onnx"
    onnx.write_bytes(b"fake-onnx")
    wwwroot = tmp_path / "wwwroot"
    metadata = build_model_metadata(
        model_id="My Model",
        display_name="Mein Modell",
        description="Testmodell",
        object_type="coin",
        currency="EUR",
        use_case="segmentation",
        profile="general",
        version="1.2.3",
    )

    result = install_model_into_pwa(
        onnx_path=onnx,
        pwa_wwwroot=wwwroot,
        metadata=metadata,
    )

    assert result.model_id == "my-model"
    assert (wwwroot / "models" / "my-model" / "coin-segmentation.onnx").read_bytes() == b"fake-onnx"
    model_json = json.loads(
        (wwwroot / "models" / "my-model" / "model.json").read_text(encoding="utf-8")
    )
    assert model_json["contract"] == "mcs-segmentation-512-letterbox-v1"
    assert model_json["input"]["shape"] == [1, 3, 512, 512]
    assert model_json["output"]["shape"] == [1, 1, 512, 512]

    manifest = json.loads((wwwroot / "models" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schemaVersion"] == MODEL_INDEX_SCHEMA_VERSION
    assert manifest["defaultModelId"] == "my-model"
    assert manifest["models"][0]["id"] == "my-model"
    assert manifest["models"][0]["modelUrl"] == "models/my-model/coin-segmentation.onnx"
    assert manifest["models"][0]["metadataUrl"] == "models/my-model/model.json"


def test_install_model_backs_up_existing_model_and_legacy_onnx(tmp_path: Path) -> None:
    onnx = tmp_path / "model.onnx"
    onnx.write_bytes(b"new")
    wwwroot = tmp_path / "wwwroot"
    old_dir = wwwroot / "models" / "my-model"
    old_dir.mkdir(parents=True)
    (old_dir / "old.txt").write_text("old", encoding="utf-8")
    (wwwroot / "models" / "coin-segmentation.onnx").write_bytes(b"legacy")
    metadata = build_model_metadata(model_id="my-model", display_name="My Model")

    result = install_model_into_pwa(
        onnx_path=onnx,
        pwa_wwwroot=wwwroot,
        metadata=metadata,
        backup_existing=True,
    )

    assert (result.model_dir / "coin-segmentation.onnx").read_bytes() == b"new"
    assert len(result.backups) == 2
    assert any(path.is_dir() and (path / "old.txt").exists() for path in result.backups)
    assert any(path.is_file() and path.read_bytes() == b"legacy" for path in result.backups)


def test_install_model_can_refuse_overwrite(tmp_path: Path) -> None:
    onnx = tmp_path / "model.onnx"
    onnx.write_bytes(b"new")
    wwwroot = tmp_path / "wwwroot"
    (wwwroot / "models" / "my-model").mkdir(parents=True)
    metadata = build_model_metadata(model_id="my-model", display_name="My Model")

    with pytest.raises(FileExistsError):
        install_model_into_pwa(
            onnx_path=onnx,
            pwa_wwwroot=wwwroot,
            metadata=metadata,
            backup_existing=False,
        )
