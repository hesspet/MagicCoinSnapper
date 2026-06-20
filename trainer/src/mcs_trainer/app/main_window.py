from __future__ import annotations

import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image
from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QRadioButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from mcs_trainer.dataset.annotated_dataset import (
    load_annotated,
    save_annotated,
)
from mcs_trainer.dataset.raw_zip import import_raw_zip
from mcs_trainer.dataset.schemas import (
    ANNOTATED_SCHEMA_VERSION,
    AnnotatedMetadata,
    AnnotatedSample,
)
from mcs_trainer.dataset.validation import validate_annotated
from mcs_trainer.app.image_viewer import ImageViewer
from mcs_trainer.app.mask_editor import MaskEditor
from mcs_trainer.app.metadata_panel import MetadataPanel


_ANNOTATED_ROOT = Path("trainer/data/annotated")
_RAW_ROOT = Path("trainer/data/raw")


class MainWindow(QMainWindow):
    """Hauptfenster der Trainer-GUI."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("MagicCoinSnapper Trainer")
        self._dataset_dir: Optional[Path] = None
        self._metadata: Optional[AnnotatedMetadata] = None
        self._index: int = -1
        self._dirty: bool = False
        self._mask_cache: dict[str, bytes] = {}

        self._editor = MaskEditor()
        self._viewer = ImageViewer(self._editor)
        self._viewer.maskEdited.connect(self._on_mask_edited)

        self._metadata_panel = MetadataPanel()
        self._metadata_panel.changed.connect(self._on_metadata_changed)

        self._tool_group = QButtonGroup(self)
        self._brush_radio = QRadioButton("Pinsel (B)")
        self._eraser_radio = QRadioButton("Radierer (E)")
        self._ellipse_radio = QRadioButton("Ellipse (O)")
        self._tool_group.addButton(self._brush_radio)
        self._tool_group.addButton(self._eraser_radio)
        self._tool_group.addButton(self._ellipse_radio)
        self._brush_radio.setChecked(True)
        self._brush_radio.toggled.connect(self._on_tool_changed)
        self._eraser_radio.toggled.connect(self._on_tool_changed)
        self._ellipse_radio.toggled.connect(self._on_tool_changed)

        self._radius_slider = QSlider(Qt.Orientation.Horizontal)
        self._radius_slider.setRange(1, 200)
        self._radius_slider.setValue(20)
        self._radius_spin = QSpinBox()
        self._radius_spin.setRange(1, 200)
        self._radius_spin.setValue(20)
        self._radius_spin.valueChanged.connect(self._radius_slider.setValue)
        self._radius_slider.valueChanged.connect(self._radius_spin.setValue)
        self._radius_slider.valueChanged.connect(self._on_radius_changed)

        self._image_list = QListWidget()
        self._image_list.currentRowChanged.connect(self._on_sample_selected)

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._train_process: Optional[QProcess] = None
        self._train_log = QPlainTextEdit()
        self._train_log.setReadOnly(True)
        self._train_dock = QDockWidget("Trainings-Log", self)
        self._train_dock.setWidget(self._train_log)
        self._train_dock.setObjectName("TrainLogDock")

        self._build_layout()
        self._build_actions()
        self._build_shortcuts()
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._train_dock)
        self._train_dock.setVisible(False)
        self._refresh_state()

    def _build_layout(self) -> None:
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(4, 4, 4, 4)
        ll.addWidget(QLabel("Bilder"))
        ll.addWidget(self._image_list, stretch=1)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 6, 6, 6)
        rl.addWidget(self._metadata_panel)
        rl.addWidget(QLabel("Werkzeug"))
        rl.addWidget(self._brush_radio)
        rl.addWidget(self._eraser_radio)
        rl.addWidget(self._ellipse_radio)
        rh = QHBoxLayout()
        rh.addWidget(QLabel("Radius"))
        rh.addWidget(self._radius_slider, stretch=1)
        rh.addWidget(self._radius_spin)
        rl.addLayout(rh)
        rl.addStretch(1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(self._viewer)
        splitter.addWidget(right)
        splitter.setSizes([220, 700, 260])
        splitter.setStretchFactor(1, 2)
        self.setCentralWidget(splitter)
        self.resize(1280, 800)

    def _build_actions(self) -> None:
        tb = QToolBar("Hauptleiste")
        tb.setMovable(False)
        self.addToolBar(tb)

        self._act_import = QAction("Raw-ZIP importieren", self)
        self._act_import.triggered.connect(self._do_import_raw)
        tb.addAction(self._act_import)

        self._act_open = QAction("Dataset oeffnen", self)
        self._act_open.triggered.connect(self._do_open_dataset)
        tb.addAction(self._act_open)

        self._act_save = QAction("Dataset speichern", self)
        self._act_save.setShortcut(QKeySequence("Ctrl+S"))
        self._act_save.triggered.connect(self._do_save)
        tb.addAction(self._act_save)

        self._act_export = QAction("Export ZIP", self)
        self._act_export.triggered.connect(self._do_export_zip)
        tb.addAction(self._act_export)

        self._act_validate = QAction("Validieren", self)
        self._act_validate.triggered.connect(self._do_validate)
        tb.addAction(self._act_validate)

        self._act_train = QAction("Training starten", self)
        self._act_train.triggered.connect(self._do_train)
        tb.addAction(self._act_train)

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence("Left"), self, activated=self._prev_sample)
        QShortcut(QKeySequence("Right"), self, activated=self._next_sample)
        QShortcut(QKeySequence("Ctrl+Z"), self, activated=self._undo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, activated=self._redo)
        QShortcut(QKeySequence("B"), self, activated=lambda: self._set_tool("brush"))
        QShortcut(QKeySequence("E"), self, activated=lambda: self._set_tool("eraser"))
        QShortcut(QKeySequence("O"), self, activated=lambda: self._set_tool("ellipse"))
        QShortcut(QKeySequence("["), self, activated=self._dec_radius)
        QShortcut(QKeySequence("]"), self, activated=self._inc_radius)

    def _set_tool(self, tool: str) -> None:
        if tool == "brush":
            self._brush_radio.setChecked(True)
        elif tool == "eraser":
            self._eraser_radio.setChecked(True)
        elif tool == "ellipse":
            self._ellipse_radio.setChecked(True)
        self._viewer.set_tool(tool)

    def _on_tool_changed(self) -> None:
        if self._brush_radio.isChecked():
            self._viewer.set_tool("brush")
        elif self._eraser_radio.isChecked():
            self._viewer.set_tool("eraser")
        elif self._ellipse_radio.isChecked():
            self._viewer.set_tool("ellipse")

    def _on_radius_changed(self, value: int) -> None:
        self._viewer.set_radius(value)

    def _dec_radius(self) -> None:
        self._radius_slider.setValue(max(1, self._radius_slider.value() - 2))

    def _inc_radius(self) -> None:
        self._radius_slider.setValue(min(200, self._radius_slider.value() + 2))

    def _refresh_state(self) -> None:
        if self._metadata is None:
            self._status.showMessage("Kein Dataset geladen")
            self._metadata_panel.clear_panel()
            return
        total = len(self._metadata.samples)
        cur = self._index + 1 if 0 <= self._index < total else 0
        self._status.showMessage(
            f"Bild {cur}/{total}  |  "
            f"{'ungespeichert' if self._dirty else 'gespeichert'}"
        )

    def _rebuild_list(self) -> None:
        self._image_list.blockSignals(True)
        self._image_list.clear()
        if self._metadata is not None:
            for s in self._metadata.samples:
                self._image_list.addItem(QListWidgetItem(s.id))
        self._image_list.blockSignals(False)

    def _set_dirty(self, dirty: bool) -> None:
        self._dirty = dirty
        self._refresh_state()

    def _confirm_discard_if_dirty(self) -> bool:
        if not self._dirty:
            return True
        res = QMessageBox.question(
            self,
            "Ungespeichert",
            "Es gibt ungespeicherte Aenderungen. Trotzdem fortfahren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return res == QMessageBox.StandardButton.Yes

    def _do_open_dataset(self) -> None:
        if not self._confirm_discard_if_dirty():
            return
        path = QFileDialog.getExistingDirectory(self, "Dataset oeffnen")
        if not path:
            return
        self.open_dataset_path(path)

    def _load_metadata(self, metadata: AnnotatedMetadata, dataset_dir: Path) -> None:
        self._metadata = metadata
        self._dataset_dir = dataset_dir
        self._mask_cache = {}
        self._index = -1
        self._rebuild_list()
        if metadata.samples:
            self._image_list.setCurrentRow(0)
        else:
            self._on_sample_selected(-1)
        self._set_dirty(False)

    def open_dataset_path(self, path: object) -> None:
        """Oeffnet ein Annotated-Dataset aus einem Pfad."""
        if not self._confirm_discard_if_dirty():
            return
        try:
            metadata = load_annotated(Path(str(path)))
        except Exception as exc:
            QMessageBox.critical(self, "Fehler", f"Laden fehlgeschlagen: {exc}")
            return
        self._load_metadata(metadata, Path(str(path)))

    def _do_import_raw(self) -> None:
        if not self._confirm_discard_if_dirty():
            return
        zip_path, _ = QFileDialog.getOpenFileName(
            self, "Raw-ZIP waehlen", "", "ZIP-Archive (*.zip)"
        )
        if not zip_path:
            return
        try:
            raw_result = import_raw_zip(Path(zip_path), _RAW_ROOT)
        except Exception as exc:
            QMessageBox.critical(self, "Importfehler", str(exc))
            return
        try:
            metadata = self._build_annotated_from_raw(raw_result.dataset_dir)
        except Exception as exc:
            QMessageBox.critical(
                self, "Fehler", f"Annotated-Erstellung fehlgeschlagen: {exc}"
            )
            return
        self._load_metadata(metadata, self._dataset_dir)
        if raw_result.warnings:
            QMessageBox.information(
                self,
                "Import-Hinweise",
                "\n".join(raw_result.warnings[:20]),
            )

    def _build_annotated_from_raw(self, raw_dir: Path) -> AnnotatedMetadata:
        import json

        raw_meta = json.loads((raw_dir / "metadata.json").read_text(encoding="utf-8"))
        slug = slugify_dataset_id(raw_meta.get("datasetId", "dataset"))
        ann_dir = _ANNOTATED_ROOT / slug
        (ann_dir / "images").mkdir(parents=True, exist_ok=True)
        (ann_dir / "masks").mkdir(parents=True, exist_ok=True)
        (ann_dir / "splits").mkdir(parents=True, exist_ok=True)
        existing = (ann_dir / "metadata.json")
        if existing.exists():
            existing.unlink()

        samples: list[AnnotatedSample] = []
        for rs in raw_meta.get("samples", []):
            rel_image = rs["image"].replace("\\", "/")
            basename = rel_image.split("/", 1)[-1]
            src_img = raw_dir / rel_image
            dst_img = ann_dir / "images" / basename
            shutil.copy2(src_img, dst_img)
            with Image.open(dst_img) as img:
                w, h = img.size
            mask_name = f"masks/{Path(basename).stem}.png"
            samples.append(
                AnnotatedSample(
                    id=rs["id"],
                    image=f"images/{basename}",
                    mask=mask_name,
                    width=w,
                    height=h,
                    contentType=rs.get("contentType"),
                    excluded=False,
                    notes=rs.get("notes"),
                    tags=list(rs.get("tags", [])),
                )
            )

        metadata = AnnotatedMetadata(
            schemaVersion=ANNOTATED_SCHEMA_VERSION,
            datasetId=slug,
            createdAt=datetime.now(timezone.utc),
            source=raw_meta.get("source"),
            samples=samples,
        )
        save_annotated(metadata, ann_dir)
        self._dataset_dir = ann_dir
        return metadata

    def _on_sample_selected(self, row: int) -> None:
        if self._metadata is None:
            return
        self._persist_current_to_cache()
        total = len(self._metadata.samples)
        if row < 0 or row >= total:
            self._index = -1
            self._metadata_panel.clear_panel()
            self._refresh_state()
            return
        self._index = row
        sample = self._metadata.samples[row]
        image_path = self._dataset_dir / sample.image if self._dataset_dir else Path(sample.image)
        existing_mask = self._dataset_dir / sample.mask if self._dataset_dir else None
        cached = self._mask_cache.get(sample.id)
        self._editor.set_sample(sample, image_path, existing_mask)
        if cached is not None:
            self._restore_cached_mask(sample.id, cached)
        self._viewer.set_tool(self._current_tool())
        self._viewer.set_radius(self._radius_slider.value())
        self._viewer.load_image(image_path, sample.width, sample.height)
        self._metadata_panel.load(sample)
        self._refresh_state()

    def _restore_cached_mask(self, sample_id: str, pixels: bytes) -> None:
        w = self._editor.width
        h = self._editor.height
        if w == 0 or h == 0 or len(pixels) != w * h:
            return
        self._editor._pixels = bytearray(pixels)
        self._editor._reset_stack()

    def _persist_current_to_cache(self) -> None:
        if self._metadata is None or self._index < 0:
            return
        sample = self._metadata.samples[self._index]
        if self._editor.width > 0:
            self._mask_cache[sample.id] = bytes(self._editor.pixels())
        self._apply_metadata_form_to_sample()

    def _apply_metadata_form_to_sample(self) -> None:
        if self._metadata is None or self._index < 0:
            return
        sample = self._metadata.samples[self._index]
        data = self._metadata_panel.current()
        new_sample = sample.model_copy(
            update={
                "notes": data["notes"],
                "tags": data["tags"],
                "excluded": data["excluded"],
            }
        )
        self._metadata.samples[self._index] = new_sample

    def _current_tool(self) -> str:
        if self._eraser_radio.isChecked():
            return "eraser"
        if self._ellipse_radio.isChecked():
            return "ellipse"
        return "brush"

    def _on_mask_edited(self) -> None:
        self._set_dirty(True)
        if self._metadata is not None and 0 <= self._index < len(self._metadata.samples):
            sid = self._metadata.samples[self._index].id
            self._mask_cache[sid] = bytes(self._editor.pixels())

    def _on_metadata_changed(self) -> None:
        self._apply_metadata_form_to_sample()
        self._set_dirty(True)

    def _prev_sample(self) -> None:
        if self._image_list.count() == 0:
            return
        row = self._image_list.currentRow()
        new_row = max(0, row - 1) if row >= 0 else 0
        self._image_list.setCurrentRow(new_row)

    def _next_sample(self) -> None:
        if self._image_list.count() == 0:
            return
        row = self._image_list.currentRow()
        new_row = min(self._image_list.count() - 1, row + 1) if row >= 0 else 0
        self._image_list.setCurrentRow(new_row)

    def _undo(self) -> None:
        if self._editor.undo():
            self._viewer.refresh()
            self._on_mask_edited()

    def _redo(self) -> None:
        if self._editor.redo():
            self._viewer.refresh()
            self._on_mask_edited()

    def _do_save(self) -> None:
        if self._metadata is None or self._dataset_dir is None:
            QMessageBox.information(self, "Speichern", "Kein Dataset geladen.")
            return
        self._persist_current_to_cache()
        masks_dir = self._dataset_dir / "masks"
        masks_dir.mkdir(parents=True, exist_ok=True)
        for sample in self._metadata.samples:
            pixels = self._mask_cache.get(sample.id)
            mask_path = self._dataset_dir / sample.mask
            mask_path.parent.mkdir(parents=True, exist_ok=True)
            if pixels is not None and len(pixels) == sample.width * sample.height:
                img = Image.frombytes("L", (sample.width, sample.height), pixels)
            else:
                existing = mask_path
                if existing.exists():
                    continue
                img = Image.new("L", (sample.width, sample.height), 0)
            img.save(mask_path, format="PNG")
        save_annotated(self._metadata, self._dataset_dir)
        self._set_dirty(False)

    def _do_export_zip(self) -> None:
        if self._metadata is None or self._dataset_dir is None:
            QMessageBox.information(self, "Export", "Kein Dataset geladen.")
            return
        self._do_save()
        default_name = f"mcs-annotated-dataset-{self._metadata.datasetId}.zip"
        default_path = self._dataset_dir.parent / default_name
        zip_path, _ = QFileDialog.getSaveFileName(
            self, "Export ZIP", str(default_path), "ZIP-Archive (*.zip)"
        )
        if not zip_path:
            return
        zip_p = Path(zip_path)
        with zipfile.ZipFile(zip_p, "w", zipfile.ZIP_DEFLATED) as zf:
            for sub in ("metadata.json",):
                p = self._dataset_dir / sub
                if p.exists():
                    zf.write(p, arcname=sub)
            for sub in ("images", "masks", "splits"):
                sub_dir = self._dataset_dir / sub
                if not sub_dir.is_dir():
                    continue
                for f in sub_dir.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(self._dataset_dir).as_posix()
                        zf.write(f, arcname=rel)
        QMessageBox.information(self, "Export", f"Exportiert:\n{zip_p}")

    def _do_validate(self) -> None:
        if self._dataset_dir is None:
            QMessageBox.information(self, "Validieren", "Kein Dataset geladen.")
            return
        res = validate_annotated(self._dataset_dir)
        parts = []
        if res.ok:
            parts.append("OK: keine Fehler.")
        else:
            parts.append(f"{len(res.errors)} Fehler:")
            parts.extend(f"  - {e}" for e in res.errors)
        if res.warnings:
            parts.append(f"{len(res.warnings)} Warnungen:")
            parts.extend(f"  - {w}" for w in res.warnings)
        QMessageBox.information(self, "Validierung", "\n".join(parts))

    def _do_train(self) -> None:
        if self._dataset_dir is None:
            QMessageBox.information(self, "Training", "Kein Dataset geladen.")
            return
        self._train_dock.setVisible(True)
        self._train_log.clear()
        if self._train_process is not None:
            self._train_process.kill()
            self._train_process.deleteLater()
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda: self._on_train_output(proc))
        proc.finished.connect(lambda code, status: self._on_train_finished(code))
        self._train_process = proc
        self._train_log.appendPlainText(
            f"$ mcs-trainer train --dataset {self._dataset_dir} --profile general\n"
        )
        proc.start("mcs-trainer", ["train", "--dataset", str(self._dataset_dir), "--profile", "general"])

    def _on_train_output(self, proc: QProcess) -> None:
        data = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self._train_log.appendPlainText(data)

    def _on_train_finished(self, code: int) -> None:
        self._train_log.appendPlainText(f"\n[Prozess beendet, Exit-Code {code}]")

    def closeEvent(self, event) -> None:
        if not self._confirm_discard_if_dirty():
            event.ignore()
            return
        if self._train_process is not None and self._train_process.state() != QProcess.ProcessState.NotRunning:
            self._train_process.kill()
            self._train_process.waitForFinished(3000)
        event.accept()
