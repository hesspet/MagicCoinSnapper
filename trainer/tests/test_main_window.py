from __future__ import annotations

import json
import os
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from mcs_trainer.app import main_window
from mcs_trainer.app.main_window import MainWindow, TrainingConfigDialog
from mcs_trainer.dataset.schemas import RAW_SCHEMA_VERSION

from conftest import build_annotated_dataset


@pytest.fixture
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_training_config_hides_cuda_when_unavailable(
    app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    dialog = TrainingConfigDialog()

    devices = [dialog.device.itemText(i) for i in range(dialog.device.count())]
    assert devices == ["auto", "cpu"]


def test_training_config_offers_cuda_when_available(
    app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    dialog = TrainingConfigDialog()

    devices = [dialog.device.itemText(i) for i in range(dialog.device.count())]
    assert devices == ["auto", "cpu", "cuda"]


@pytest.fixture
def messages(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str]]:
    captured: list[tuple[str, str, str]] = []

    def capture(_parent: object, title: str, text: str) -> None:
        captured.append(("info", title, text))

    def capture_error(_parent: object, title: str, text: str) -> None:
        captured.append(("critical", title, text))

    monkeypatch.setattr(QMessageBox, "information", capture)
    monkeypatch.setattr(QMessageBox, "critical", capture_error)
    return captured


def test_open_dataset_path_rejects_raw_schema(
    tmp_path: Path,
    app: QApplication,
    messages: list[tuple[str, str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "metadata.json").write_text(
        json.dumps({"schemaVersion": RAW_SCHEMA_VERSION}), encoding="utf-8"
    )
    monkeypatch.setattr(
        main_window,
        "load_annotated",
        lambda _path: pytest.fail("raw dataset must not be loaded as annotated"),
    )

    window = MainWindow()
    window.open_dataset_path(raw_dir)

    assert messages == [
        (
            "info",
            "Dataset oeffnen",
            "Raw-Dataset erkannt. Bitte Raw-ZIP importieren.",
        )
    ]


def test_open_dataset_path_reports_missing_schema(
    tmp_path: Path,
    app: QApplication,
    messages: list[tuple[str, str, str]],
) -> None:
    dataset_dir = tmp_path / "missing-schema"
    dataset_dir.mkdir()
    (dataset_dir / "metadata.json").write_text("{}", encoding="utf-8")

    window = MainWindow()
    window.open_dataset_path(dataset_dir)

    assert messages == [("critical", "Fehler", "schemaVersion fehlt in metadata.json.")]


def test_clear_mask_action_clears_cache_and_marks_dirty(
    tmp_path: Path,
    app: QApplication,
    messages: list[tuple[str, str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_dir = build_annotated_dataset(
        tmp_path, "ds-gui", [{"id": "s1", "width": 8, "height": 8}]
    )
    window = MainWindow()
    window.open_dataset_path(dataset_dir)
    window._editor.paint((4, 4), 2)
    refreshed = False

    def refresh() -> None:
        nonlocal refreshed
        refreshed = True

    monkeypatch.setattr(window._viewer, "refresh", refresh)

    window._act_clear_mask.trigger()

    assert refreshed
    assert window._dirty is True
    assert set(window._editor.pixels()) == {0}
    assert window._mask_cache["s1"] == bytes(64)


def test_next_action_uses_next_sample(
    tmp_path: Path,
    app: QApplication,
    messages: list[tuple[str, str, str]],
) -> None:
    dataset_dir = build_annotated_dataset(
        tmp_path,
        "ds-next",
        [
            {"id": "s1", "width": 8, "height": 8},
            {"id": "s2", "width": 8, "height": 8},
        ],
    )
    window = MainWindow()
    window.open_dataset_path(dataset_dir)

    window._act_next.trigger()

    assert window._image_list.currentRow() == 1


def test_save_shows_dataset_path(
    tmp_path: Path,
    app: QApplication,
    messages: list[tuple[str, str, str]],
) -> None:
    dataset_dir = build_annotated_dataset(
        tmp_path, "ds-save", [{"id": "s1", "width": 8, "height": 8}]
    )
    window = MainWindow()
    window.open_dataset_path(dataset_dir)

    window._do_save()

    assert messages == [
        (
            "info",
            "Dataset speichern",
            f"Dataset gespeichert:\n{dataset_dir}",
        )
    ]
