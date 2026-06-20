from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from mcs_trainer.dataset.schemas import AnnotatedSample


class MetadataPanel(QWidget):
    """Formular fuer Notizen, Tags und excluded-Flag eines Samples."""

    changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        self._id_label = QLabel("-")
        outer.addWidget(self._id_label)

        form = QFormLayout()
        self._notes = QTextEdit()
        self._notes.setFixedHeight(80)
        self._tags = QLineEdit()
        self._tags.setPlaceholderText("tag1, tag2, ...")
        self._excluded = QCheckBox("ausgeschlossen")
        form.addRow("Notizen:", self._notes)
        form.addRow("Tags:", self._tags)
        form.addRow("", self._excluded)
        outer.addLayout(form)

        self._notes.textChanged.connect(self._emit_changed)
        self._tags.textChanged.connect(self._emit_changed)
        self._excluded.toggled.connect(self._emit_changed)
        self._loading = False

    def _emit_changed(self) -> None:
        if not self._loading:
            self.changed.emit()

    def load(self, sample: AnnotatedSample) -> None:
        self._loading = True
        self._id_label.setText(f"ID: {sample.id}")
        self._notes.setPlainText(sample.notes or "")
        self._tags.setText(", ".join(sample.tags))
        self._excluded.setChecked(sample.excluded)
        self._loading = False

    def current(self) -> dict:
        tags_raw = self._tags.text().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        return {
            "notes": self._notes.toPlainText().strip() or None,
            "tags": tags,
            "excluded": self._excluded.isChecked(),
        }

    def clear_panel(self) -> None:
        self._loading = True
        self._id_label.setText("-")
        self._notes.clear()
        self._tags.clear()
        self._excluded.setChecked(False)
        self._loading = False
