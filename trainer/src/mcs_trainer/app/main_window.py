from __future__ import annotations

import shutil
import sys
import zipfile
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image
from PySide6.QtCore import QProcess, QProcessEnvironment, Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from mcs_trainer import __version__
from mcs_trainer.dataset.annotated_dataset import (
    load_annotated,
    save_annotated,
)
from mcs_trainer.dataset.raw_zip import import_raw_zip
from mcs_trainer.dataset.schemas import (
    ANNOTATED_SCHEMA_VERSION,
    AnnotatedMetadata,
    AnnotatedSample,
    RAW_SCHEMA_VERSION,
)
from mcs_trainer.app.image_viewer import ImageViewer
from mcs_trainer.app.mask_editor import MaskEditor
from mcs_trainer.app.metadata_panel import MetadataPanel
from mcs_trainer.app import workflow
from mcs_trainer.ml.progress import format_duration, parse_train_progress
from mcs_trainer.utils.paths import slugify_dataset_id


_ANNOTATED_ROOT = Path("trainer/data/annotated")
_RAW_ROOT = Path("trainer/data/raw")


def _cuda_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


class TrainingConfigDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Training konfigurieren")
        layout = QFormLayout(self)

        self.profile = QLineEdit("general")
        self.device = QComboBox()
        cuda_available = _cuda_available()
        self.device.addItems(["auto", "cpu"] + (["cuda"] if cuda_available else []))
        self.epochs = QSpinBox()
        self.epochs.setRange(1, 10000)
        self.epochs.setValue(30)
        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 1024)
        self.batch_size.setValue(8)
        self.lr = QDoubleSpinBox()
        self.lr.setDecimals(6)
        self.lr.setRange(0.000001, 10.0)
        self.lr.setValue(0.001)

        layout.addRow("Profil", self.profile)
        layout.addRow("Geraet", self.device)
        if not cuda_available:
            layout.addRow("", QLabel("CUDA nicht verfuegbar; auto nutzt CPU."))
        layout.addRow("Epochen", self.epochs)
        layout.addRow("Batch-Groesse", self.batch_size)
        layout.addRow("Lernrate", self.lr)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def values(self) -> dict[str, object]:
        return {
            "profile": self.profile.text().strip() or "general",
            "device": self.device.currentText(),
            "epochs": self.epochs.value(),
            "batch_size": self.batch_size.value(),
            "lr": self.lr.value(),
        }


class ModelMetadataDialog(QDialog):
    def __init__(
        self,
        default_id: str,
        default_profile: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Modelldaten")
        layout = QFormLayout(self)

        self.model_id = QLineEdit(default_id)
        self.display_name = QLineEdit("Coin Segmentation")
        self.description = QLineEdit("Segmentierungsmodell fuer MagicCoinSnapper")
        self.object_type = QLineEdit("coin")
        self.currency = QLineEdit("unknown")
        self.use_case = QLineEdit("segmentation")
        self.profile = QLineEdit(default_profile)
        self.version = QLineEdit(__version__)

        layout.addRow("ID", self.model_id)
        layout.addRow("Anzeigename", self.display_name)
        layout.addRow("Beschreibung", self.description)
        layout.addRow("Objekttyp", self.object_type)
        layout.addRow("Waehrung", self.currency)
        layout.addRow("Einsatz", self.use_case)
        layout.addRow("Profil", self.profile)
        layout.addRow("Version", self.version)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def metadata(self) -> dict[str, str]:
        model_id = self.model_id.text().strip() or "coin-segmentation"
        return workflow.build_model_metadata(
            model_id=model_id,
            display_name=self.display_name.text().strip() or model_id,
            description=self.description.text().strip(),
            object_type=self.object_type.text().strip() or "coin",
            currency=self.currency.text().strip() or "unknown",
            use_case=self.use_case.text().strip() or "segmentation",
            profile=self.profile.text().strip() or "general",
            version=self.version.text().strip() or __version__,
        )


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
        self._latest_run_dir: Optional[Path] = None
        self._latest_onnx_path: Optional[Path] = None
        self._latest_package_path: Optional[Path] = None
        self._last_train_out_dir = Path("trainer/runs/coinseg")
        self._last_train_profile = "general"
        self._training_active = False
        self._train_output_buffer = ""

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
        self._train_status = QLabel("")
        self._status.addPermanentWidget(self._train_status)

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
        ellipse_help = QLabel(
            "Ellipse: Rahmen ziehen, Griffe/Innenbereich anpassen, dann uebernehmen. "
            "Pfeiltasten bewegen, Shift+Pfeile skalieren, Enter uebernimmt, Esc verwirft."
        )
        ellipse_help.setWordWrap(True)
        rl.addWidget(ellipse_help)
        ellipse_apply = QPushButton("Ellipse uebernehmen")
        ellipse_apply.clicked.connect(self._viewer.apply_ellipse_frame)
        rl.addWidget(ellipse_apply)
        ellipse_discard = QPushButton("Rahmen verwerfen")
        ellipse_discard.clicked.connect(self._viewer.clear_ellipse_frame)
        rl.addWidget(ellipse_discard)
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
        self._act_save.triggered.connect(lambda _checked=False: self._do_save())
        tb.addAction(self._act_save)

        self._act_export = QAction("Dataset ZIP exportieren", self)
        self._act_export.triggered.connect(self._do_export_zip)
        tb.addAction(self._act_export)

        tb.addSeparator()

        self._act_clear_mask = QAction("Maske leeren", self)
        self._act_clear_mask.triggered.connect(self._clear_mask)
        tb.addAction(self._act_clear_mask)

        self._act_next = QAction("Weiter", self)
        self._act_next.triggered.connect(self._next_sample)
        tb.addAction(self._act_next)

        tb.addSeparator()

        self._act_validate = QAction("Daten pruefen", self)
        self._act_validate.triggered.connect(self._do_validate)
        tb.addAction(self._act_validate)

        self._act_split = QAction("Daten aufteilen", self)
        self._act_split.triggered.connect(self._do_split)
        tb.addAction(self._act_split)

        self._act_train = QAction("Training starten (config)", self)
        self._act_train.triggered.connect(self._do_train)
        tb.addAction(self._act_train)

        self._act_evaluate = QAction("Modell testen", self)
        self._act_evaluate.triggered.connect(self._do_evaluate)
        tb.addAction(self._act_evaluate)

        self._act_export_onnx = QAction("ONNX exportieren", self)
        self._act_export_onnx.triggered.connect(self._do_export_onnx)
        tb.addAction(self._act_export_onnx)

        self._act_package_model = QAction("Modellpaket erstellen", self)
        self._act_package_model.triggered.connect(self._do_package_model)
        tb.addAction(self._act_package_model)

        self._act_install_model = QAction("Modell in PWA uebernehmen", self)
        self._act_install_model.triggered.connect(self._do_install_model)
        tb.addAction(self._act_install_model)

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
        if self._training_active:
            return
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
        dataset_dir = Path(str(path))
        meta_path = dataset_dir / "metadata.json"
        if not meta_path.exists():
            QMessageBox.critical(self, "Fehler", "metadata.json fehlt.")
            return
        try:
            raw_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Fehler", "metadata.json ist kein gueltiges JSON.")
            return
        except Exception as exc:
            QMessageBox.critical(self, "Fehler", f"metadata.json konnte nicht gelesen werden: {exc}")
            return
        if not isinstance(raw_meta, dict):
            QMessageBox.critical(self, "Fehler", "metadata.json ist ungueltig.")
            return
        schema = raw_meta.get("schemaVersion")
        if schema == RAW_SCHEMA_VERSION:
            QMessageBox.information(
                self,
                "Dataset oeffnen",
                "Raw-Dataset erkannt. Bitte Raw-ZIP importieren.",
            )
            return
        if schema != ANNOTATED_SCHEMA_VERSION:
            if schema is None:
                msg = "schemaVersion fehlt in metadata.json."
            else:
                msg = f"Unbekannte schemaVersion: {schema}"
            QMessageBox.critical(self, "Fehler", msg)
            return
        try:
            metadata = load_annotated(dataset_dir)
        except Exception:
            QMessageBox.critical(
                self,
                "Fehler",
                "Annotated-Dataset ist ungueltig. Bitte metadata.json pruefen.",
            )
            return
        self._load_metadata(metadata, dataset_dir)

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

    def _clear_mask(self) -> None:
        if self._metadata is None or self._index < 0 or self._editor.width == 0:
            return
        self._editor.clear()
        self._viewer.refresh()
        self._on_mask_edited()

    def _undo(self) -> None:
        if self._editor.undo():
            self._viewer.refresh()
            self._on_mask_edited()

    def _redo(self) -> None:
        if self._editor.redo():
            self._viewer.refresh()
            self._on_mask_edited()

    def _do_save(self, show_message: bool = True) -> None:
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
        if show_message:
            QMessageBox.information(
                self,
                "Dataset speichern",
                f"Dataset gespeichert:\n{self._dataset_dir}",
            )

    def _do_export_zip(self) -> None:
        if self._metadata is None or self._dataset_dir is None:
            QMessageBox.information(self, "Export", "Kein Dataset geladen.")
            return
        self._do_save(show_message=False)
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
            QMessageBox.information(self, "Daten pruefen", "Kein Dataset geladen.")
            return
        res = workflow.validate_annotated_dataset(self._dataset_dir)
        parts = []
        if res.ok:
            parts.append("OK: keine Fehler.")
        else:
            parts.append(f"{len(res.errors)} Fehler:")
            parts.extend(f"  - {e}" for e in res.errors)
        if res.warnings:
            parts.append(f"{len(res.warnings)} Warnungen:")
            parts.extend(f"  - {w}" for w in res.warnings)
        QMessageBox.information(self, "Daten pruefen", "\n".join(parts))

    def _do_split(self) -> None:
        if self._dataset_dir is None:
            QMessageBox.information(self, "Daten aufteilen", "Kein Dataset geladen.")
            return
        if self._dirty:
            self._do_save(show_message=False)
        try:
            result = workflow.split_dataset(self._dataset_dir)
        except Exception as exc:
            QMessageBox.critical(self, "Daten aufteilen", str(exc))
            return
        QMessageBox.information(
            self,
            "Daten aufteilen",
            "Splits erstellt:\n"
            f"Train: {result.train_count}\n"
            f"Val: {result.val_count}\n"
            f"Test: {result.test_count}",
        )

    def _do_train(self) -> None:
        if self._dataset_dir is None:
            QMessageBox.information(self, "Training", "Kein Dataset geladen.")
            return
        dialog = TrainingConfigDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        config = dialog.values()
        if self._dirty:
            self._do_save(show_message=False)
        self._train_dock.setVisible(True)
        self._train_log.clear()
        self._training_active = True
        self._train_output_buffer = ""
        self._train_status.setText("Training startet...")
        if self._train_process is not None:
            self._train_process.kill()
            self._train_process.deleteLater()
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda: self._on_train_output(proc))
        proc.finished.connect(lambda code, status: self._on_train_finished(code, status))
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        proc.setProcessEnvironment(env)
        self._train_process = proc
        self._last_train_profile = str(config["profile"])
        self._last_train_out_dir = Path("trainer/runs/coinseg")
        args = [
            "-u",
            "-m",
            "mcs_trainer.cli.main",
            "train",
            "--dataset",
            str(self._dataset_dir),
            "--profile",
            self._last_train_profile,
            "--device",
            str(config["device"]),
            "--epochs",
            str(config["epochs"]),
            "--batch-size",
            str(config["batch_size"]),
            "--lr",
            str(config["lr"]),
            "--out-dir",
            str(self._last_train_out_dir),
        ]
        self._train_log.appendPlainText(f"$ {sys.executable} {' '.join(args)}\n")
        proc.start(sys.executable, args)

    def _do_evaluate(self) -> None:
        if self._dataset_dir is None:
            QMessageBox.information(self, "Modell testen", "Kein Dataset geladen.")
            return
        run_dir = self._select_run_dir("Run-Verzeichnis fuer Test waehlen")
        if run_dir is None:
            return
        try:
            result = workflow.evaluate_model(run_dir, self._dataset_dir)
        except Exception as exc:
            QMessageBox.critical(self, "Modell testen", str(exc))
            return
        QMessageBox.information(
            self,
            "Modell testen",
            f"Loss: {result.loss:.4f}\n"
            f"Dice: {result.dice:.4f}\n"
            f"IoU: {result.iou:.4f}\n"
            f"Samples: {result.n_samples}",
        )

    def _do_export_onnx(self) -> None:
        run_dir = self._select_run_dir("Run-Verzeichnis fuer ONNX-Export waehlen")
        if run_dir is None:
            return
        try:
            onnx_path = workflow.export_onnx_model(run_dir)
        except Exception as exc:
            QMessageBox.critical(self, "ONNX exportieren", str(exc))
            return
        self._latest_run_dir = run_dir
        self._latest_onnx_path = onnx_path
        QMessageBox.information(self, "ONNX exportieren", f"Exportiert:\n{onnx_path}")

    def _do_package_model(self) -> None:
        run_dir = self._select_run_dir("Run-Verzeichnis fuer Modellpaket waehlen")
        if run_dir is None:
            return
        onnx_path = self._select_onnx_path("ONNX-Datei fuer Modellpaket waehlen")
        if onnx_path is None:
            return
        metadata = self._prompt_model_metadata(run_dir)
        if metadata is None:
            return
        try:
            package_path = workflow.package_trained_model(
                onnx_path=onnx_path,
                run_dir=run_dir,
                metadata=metadata,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Modellpaket erstellen", str(exc))
            return
        self._latest_run_dir = run_dir
        self._latest_onnx_path = onnx_path
        self._latest_package_path = package_path
        QMessageBox.information(
            self, "Modellpaket erstellen", f"Paket erstellt:\n{package_path}"
        )

    def _do_install_model(self) -> None:
        onnx_path = self._select_onnx_path("ONNX-Datei fuer PWA-Uebernahme waehlen")
        if onnx_path is None:
            return
        metadata = self._prompt_model_metadata(self._latest_run_dir)
        if metadata is None:
            return
        default_root = workflow.default_pwa_wwwroot()
        pwa_path = QFileDialog.getExistingDirectory(
            self,
            "PWA-wwwroot waehlen",
            str(default_root),
        )
        if not pwa_path:
            return
        exists = workflow.model_install_targets_exist(pwa_path, metadata["id"])
        action = "ersetzen" if exists else "installieren"
        res = QMessageBox.question(
            self,
            "Modell in PWA uebernehmen",
            f"Modell '{metadata['id']}' in die PWA {action}?\n\n"
            "Vorhandene Dateien werden automatisch mit Zeitstempel gesichert.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if res != QMessageBox.StandardButton.Yes:
            return
        try:
            result = workflow.install_model(
                onnx_path=onnx_path,
                pwa_wwwroot=Path(pwa_path),
                metadata=metadata,
                backup_existing=True,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Modell in PWA uebernehmen", str(exc))
            return
        backup_text = "\n".join(str(p) for p in result.backups) or "Keine"
        QMessageBox.information(
            self,
            "Modell in PWA uebernehmen",
            f"Installiert:\n{result.model_dir}\n\nManifest:\n{result.manifest_path}\n\nBackups:\n{backup_text}",
        )

    def _select_run_dir(self, title: str) -> Optional[Path]:
        if self._latest_run_dir is not None and self._latest_run_dir.exists():
            return self._latest_run_dir
        newest = workflow.find_newest_run(self._last_train_out_dir, self._last_train_profile)
        if newest is not None:
            self._latest_run_dir = newest
            return newest
        path = QFileDialog.getExistingDirectory(self, title, str(self._last_train_out_dir))
        return Path(path) if path else None

    def _select_onnx_path(self, title: str) -> Optional[Path]:
        if self._latest_onnx_path is not None and self._latest_onnx_path.exists():
            return self._latest_onnx_path
        if self._latest_run_dir is not None:
            candidate = self._latest_run_dir / "coin-segmentation.onnx"
            if candidate.exists():
                self._latest_onnx_path = candidate
                return candidate
        file_path, _ = QFileDialog.getOpenFileName(
            self, title, "", "ONNX-Modelle (*.onnx);;Alle Dateien (*)"
        )
        return Path(file_path) if file_path else None

    def _prompt_model_metadata(self, run_dir: Optional[Path]) -> Optional[dict]:
        profile = self._profile_from_run(run_dir) or self._last_train_profile
        base = self._metadata.datasetId if self._metadata is not None else "coin-segmentation"
        default_id = slugify_dataset_id(f"{base}-{profile}")
        dialog = ModelMetadataDialog(default_id, profile, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.metadata()

    def _profile_from_run(self, run_dir: Optional[Path]) -> Optional[str]:
        if run_dir is None:
            return None
        try:
            import json

            meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            profile = meta.get("profile")
            return str(profile) if profile else None
        except Exception:
            return None

    def _on_train_output(self, proc: QProcess) -> None:
        data = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self._train_log.appendPlainText(data)
            self._train_output_buffer += data
            lines = self._train_output_buffer.splitlines(keepends=True)
            if lines and not lines[-1].endswith(("\n", "\r")):
                self._train_output_buffer = lines.pop()
            else:
                self._train_output_buffer = ""
            for line in lines:
                self._update_train_status_from_line(line.strip())

    def _update_train_status_from_line(self, line: str) -> None:
        progress = parse_train_progress(line)
        if progress is not None:
            self._train_status.setText(
                "Training: "
                f"Epoche {progress.epoch}/{progress.total} "
                f"({progress.percent:.1f}%, ETA {format_duration(progress.eta_s)})"
            )
            return
        if line.startswith("TRAIN_FAILED"):
            self._train_status.setText("Training fehlgeschlagen")
        elif line.startswith("TRAIN_DONE"):
            self._train_status.setText("Training abgeschlossen")

    def _on_train_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        newest = workflow.find_newest_run(self._last_train_out_dir, self._last_train_profile)
        if code == 0 and status == QProcess.ExitStatus.NormalExit and newest is not None:
            self._latest_run_dir = newest
            candidate = newest / "coin-segmentation.onnx"
            if candidate.exists():
                self._latest_onnx_path = candidate
            self._train_log.appendPlainText(f"\nLetzter Run: {newest}")
            self._train_status.setText(f"Training abgeschlossen: {newest}")
        else:
            self._train_status.setText(f"Training fehlgeschlagen (Exit-Code {code})")
            self._train_log.appendPlainText(
                f"\nTraining fehlgeschlagen (Exit-Code {code})"
            )
        self._training_active = False
        self._train_log.appendPlainText(f"\n[Prozess beendet, Exit-Code {code}]")
        self._refresh_state()

    def closeEvent(self, event) -> None:
        if not self._confirm_discard_if_dirty():
            event.ignore()
            return
        if self._train_process is not None and self._train_process.state() != QProcess.ProcessState.NotRunning:
            self._train_process.kill()
            self._train_process.waitForFinished(3000)
        event.accept()
