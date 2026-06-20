from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QTransform,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

from mcs_trainer.app.mask_editor import MaskEditor


class ImageViewer(QGraphicsView):
    """Zeigt das aktuelle Bild an und erlaubt das Malen auf der Masken-Ebene."""

    maskEdited = Signal()

    def __init__(self, mask_editor: MaskEditor, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self._editor = mask_editor
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setAcceptDrops(False)

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._overlay_item: Optional[QGraphicsPixmapItem] = None
        self._rubber_item: Optional[QGraphicsRectItem] = None

        self._panning: bool = False
        self._pan_last: Optional[object] = None
        self._painting: bool = False
        self._last_pos: Optional[object] = None
        self._drawing_ellipse: bool = False
        self._ellipse_start: Optional[object] = None

        self._tool: str = "brush"
        self._radius: int = 20
        self._scale: float = 1.0

    def set_tool(self, tool: str) -> None:
        self._tool = tool

    def set_radius(self, radius: int) -> None:
        self._radius = max(1, int(radius))

    def tool(self) -> str:
        return self._tool

    def radius(self) -> int:
        return self._radius

    def load_image(self, image_path: object, width: int, height: int) -> None:
        self._scene.clear()
        self._pixmap_item = None
        self._overlay_item = None
        self._rubber_item = None

        pm = QPixmap(str(image_path))
        if pm.isNull():
            return
        self._pixmap_item = self._scene.addPixmap(pm)
        self._scene.setSceneRect(QRectF(0, 0, pm.width(), pm.height()))

        overlay = QImage(width, height, QImage.Format.Format_ARGB32)
        overlay.fill(QColor(0, 0, 0, 0))
        self._overlay_item = self._scene.addPixmap(QPixmap.fromImage(overlay))
        self._overlay_item.setZValue(1.0)

        self._refresh_overlay()
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self._scale = self.transform().m11()

    def _refresh_overlay(self) -> None:
        if self._overlay_item is None:
            return
        w = self._editor.width
        h = self._editor.height
        if w == 0 or h == 0:
            return
        overlay = QImage(w, h, QImage.Format.Format_ARGB32)
        overlay.fill(QColor(0, 0, 0, 0))
        pixels = self._editor.pixels()
        for y in range(h):
            for x in range(w):
                v = pixels[y * w + x]
                if v == 255:
                    overlay.setPixelColor(x, y, QColor(0, 255, 0, 160))
                else:
                    overlay.setPixelColor(x, y, QColor(0, 0, 0, 0))
        self._overlay_item.setPixmap(QPixmap.fromImage(overlay))

    def _map_to_image(self, pos: object) -> Optional[object]:
        if self._pixmap_item is None:
            return None
        scene_pos = self.mapToScene(pos)
        if scene_pos is None:
            return None
        x = int(scene_pos.x())
        y = int(scene_pos.y())
        if not (0 <= x < self._editor.width and 0 <= y < self._editor.height):
            return None
        return (x, y)

    def _begin_stroke(self, pos: object) -> None:
        if self._tool == "ellipse":
            self._drawing_ellipse = True
            self._ellipse_start = self._map_to_image(pos)
            if self._ellipse_start is not None:
                x, y = self._ellipse_start
                self._rubber_item = QGraphicsRectItem(
                    QRectF(x, y, 1, 1)
                )
                pen = QPen(QColor(0, 255, 0, 200), 1)
                self._rubber_item.setPen(pen)
                self._rubber_item.setBrush(QBrush(QColor(0, 255, 0, 60)))
                self._rubber_item.setZValue(2.0)
                self._scene.addItem(self._rubber_item)
            return

        img_pos = self._map_to_image(pos)
        if img_pos is None:
            return
        self._painting = True
        self._last_pos = img_pos
        self._editor.paint(img_pos, self._radius, erase=(self._tool == "eraser"))
        self._refresh_overlay()
        self.maskEdited.emit()

    def _continue_stroke(self, pos: object) -> None:
        if self._drawing_ellipse:
            cur = self._map_to_image(pos)
            if cur is None or self._ellipse_start is None or self._rubber_item is None:
                return
            x0, y0 = self._ellipse_start
            x1, y1 = cur
            self._rubber_item.setRect(QRectF(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0)))
            return

        if not self._painting:
            return
        img_pos = self._map_to_image(pos)
        if img_pos is None:
            return
        if self._last_pos is not None:
            x0, y0 = self._last_pos
            x1, y1 = img_pos
            steps = max(abs(x1 - x0), abs(y1 - y0))
            for i in range(steps + 1):
                t = i / steps if steps else 0
                ix = int(round(x0 + (x1 - x0) * t))
                iy = int(round(y0 + (y1 - y0) * t))
                self._editor.paint((ix, iy), self._radius, erase=(self._tool == "eraser"))
        else:
            self._editor.paint(img_pos, self._radius, erase=(self._tool == "eraser"))
        self._last_pos = img_pos
        self._refresh_overlay()
        self.maskEdited.emit()

    def _end_stroke(self) -> None:
        if self._drawing_ellipse:
            self._drawing_ellipse = False
            if self._rubber_item is not None:
                rect = self._rubber_item.rect()
                self._scene.removeItem(self._rubber_item)
                self._rubber_item = None
                if self._ellipse_start is not None:
                    self._editor.paint_ellipse(
                        (
                            int(rect.x()),
                            int(rect.y()),
                            int(rect.x() + rect.width()),
                            int(rect.y() + rect.height()),
                        ),
                        erase=(self._tool == "eraser"),
                    )
                    self._refresh_overlay()
                    self.maskEdited.emit()
            self._ellipse_start = None
            return

        self._painting = False
        self._last_pos = None

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._scale *= 1.15
            else:
                self._scale /= 1.15
            self._scale = max(0.1, min(self._scale, 20.0))
            self.setTransform(self._pixmap_transform(self._scale))
            event.accept()
            return
        super().wheelEvent(event)

    def _pixmap_transform(self, scale: float) -> QTransform:
        t = QTransform()
        t.scale(scale, scale)
        return t

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_last = event.position().toPoint()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if self._tool in ("brush", "eraser", "ellipse"):
                self._begin_stroke(event.position().toPoint())
                event.accept()
                return
            self._panning = True
            self._pan_last = event.position().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._panning:
            if self._pan_last is not None:
                delta = event.position().toPoint() - self._pan_last
                self._pan_last = event.position().toPoint()
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - delta.x()
                )
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - delta.y()
                )
            event.accept()
            return
        if self._painting or self._drawing_ellipse:
            self._continue_stroke(event.position().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self._pan_last = None
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if self._painting or self._drawing_ellipse:
                self._end_stroke()
                event.accept()
                return
            self._panning = False
            self._pan_last = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)

    def refresh(self) -> None:
        self._refresh_overlay()
