from __future__ import annotations

import json
import sys
from types import SimpleNamespace
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mcs_trainer.cli import main as cli_main
from mcs_trainer.cli.main import app
from mcs_trainer.dataset.schemas import RAW_SCHEMA_VERSION

from conftest import build_annotated_dataset, build_raw_zip, make_image_bytes


runner = CliRunner()


def test_cli_version() -> None:
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "0.4.0" in res.stdout


def test_train_cuda_fails_early_when_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    res = runner.invoke(app, ["train", "--dataset", "ds", "--device", "cuda"])

    assert res.exit_code == 1
    assert "CUDA wurde angefordert" in res.stdout
    assert "TRAIN_FAILED error=CUDA wurde angefordert" in res.stdout
    assert "TRAIN_START" not in res.stdout


def test_resolve_device_auto_uses_cpu_when_cuda_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    assert cli_main._resolve_device("auto") == "cpu"


def test_cli_help() -> None:
    res = runner.invoke(app, ["--help"])
    assert res.exit_code == 0
    assert "import-raw" in res.stdout
    assert "validate" in res.stdout
    assert "split" in res.stdout


def test_cli_import_raw(tmp_path: Path) -> None:
    zip_path = tmp_path / "raw.zip"
    build_raw_zip(
        zip_path,
        samples=[
            {
                "meta": {
                    "id": "s1",
                    "image": "images/sample-1.png",
                    "width": 32,
                    "height": 32,
                    "contentType": "image/png",
                },
                "data": make_image_bytes(32, 32, "RGB", "PNG", (1, 2, 3)),
            }
        ],
        dataset_id="ds-cli",
    )

    dest = tmp_path / "dest"
    res = runner.invoke(app, ["import-raw", "--zip", str(zip_path), "--dest", str(dest)])
    assert res.exit_code == 0
    assert "ds-cli" in res.stdout
    assert (dest / "ds-cli" / "metadata.json").exists()


def test_cli_validate_raw(tmp_path: Path) -> None:
    ds = tmp_path / "ds-raw-cli"
    (ds / "images").mkdir(parents=True, exist_ok=True)
    img = make_image_bytes(40, 30, "RGB", "PNG", (1, 2, 3))
    (ds / "images" / "s1.png").write_bytes(img)
    meta = {
        "schemaVersion": RAW_SCHEMA_VERSION,
        "datasetId": "ds-raw-cli",
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "source": None,
        "samples": [
            {
                "id": "s1",
                "image": "images/s1.png",
                "width": 40,
                "height": 30,
                "contentType": "image/png",
            }
        ],
    }
    (ds / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    res = runner.invoke(app, ["validate", "--dataset", str(ds)])
    assert res.exit_code == 0
    assert "Keine Fehler" in res.stdout


def test_cli_validate_invalid(tmp_path: Path) -> None:
    ds = tmp_path / "ds-broken-cli"
    (ds / "images").mkdir(parents=True, exist_ok=True)
    meta = {
        "schemaVersion": RAW_SCHEMA_VERSION,
        "datasetId": "ds-broken-cli",
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "source": None,
        "samples": [
            {"id": "s1", "image": "images/missing.png"},
        ],
    }
    (ds / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    res = runner.invoke(app, ["validate", "--dataset", str(ds)])
    assert res.exit_code == 1
    assert "Fehler" in res.stdout


def test_cli_split(tmp_path: Path) -> None:
    specs = [{"id": f"s{i}", "width": 16, "height": 16} for i in range(8)]
    ds = build_annotated_dataset(tmp_path, "ds-split-cli", specs)

    res = runner.invoke(app, ["split", "--dataset", str(ds)])
    assert res.exit_code == 0
    assert (ds / "splits" / "train.txt").exists()
    assert (ds / "splits" / "val.txt").exists()
    assert (ds / "splits" / "test.txt").exists()
