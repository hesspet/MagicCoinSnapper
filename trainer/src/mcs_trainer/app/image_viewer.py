from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, Signal
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
    QGraphicsEllipseItem,
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
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._overlay_item: Optional[QGraphicsPixmapItem] = None
        self._frame_rect_item: Optional[QGraphicsRectItem] = None
        self._frame_ellipse_item: Optional[QGraphicsEllipseItem] = None
        self._handle_items: list[QGraphicsRectItem] = []

        self._panning: bool = False
        self._pan_last: Optional[object] = None
        self._painting: bool = False
        self._last_pos: Optional[object] = None
        self._drawing_ellipse: bool = False
        self._ellipse_start: Optional[tuple[int, int]] = None
        self._ellipse_rect: Optional[QRectF] = None
        self._ellipse_drag_mode: Optional[str] = None
        self._ellipse_drag_handle: Optional[str] = None
        self._ellipse_drag_last: Optional[tuple[int, int]] = None

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
        self._frame_rect_item = None
        self._frame_ellipse_item = None
        self._handle_items = []
        self._ellipse_rect = None
        self._drawing_ellipse = False
        self._ellipse_drag_mode = None
        self._ellipse_drag_handle = None
        self._ellipse_drag_last = None

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

    def _map_to_image_clamped(self, pos: object) -> Optional[tuple[int, int]]:
        if self._pixmap_item is None or self._editor.width == 0 or self._editor.height == 0:
            return None
        scene_pos = self.mapToScene(pos)
        x = max(0, min(self._editor.width - 1, int(scene_pos.x())))
        y = max(0, min(self._editor.height - 1, int(scene_pos.y())))
        return (x, y)

    def _clamped_frame_rect(self, rect: QRectF) -> QRectF:
        rect = rect.normalized()
        if self._editor.width == 0 or self._editor.height == 0:
            return QRectF()
        left = max(0.0, min(float(self._editor.width - 1), rect.left()))
        top = max(0.0, min(float(self._editor.height - 1), rect.top()))
        right = max(0.0, min(float(self._editor.width - 1), rect.right()))
        bottom = max(0.0, min(float(self._editor.height - 1), rect.bottom()))
        if right < left:
            left, right = right, left
        if bottom < top:
            top, bottom = bottom, top
        return QRectF(left, top, max(1.0, right - left), max(1.0, bottom - top))

    def _handle_centers(self, rect: QRectF) -> list[tuple[str, float, float]]:
        cx = rect.center().x()
        cy = rect.center().y()
        return [
            ("nw", rect.left(), rect.top()),
            ("n", cx, rect.top()),
            ("ne", rect.right(), rect.top()),
            ("e", rect.right(), cy),
            ("se", rect.right(), rect.bottom()),
            ("s", cx, rect.bottom()),
            ("sw", rect.left(), rect.bottom()),
            ("w", rect.left(), cy),
        ]

    def _sync_ellipse_frame_items(self) -> None:
        if self._ellipse_rect is None:
            return
        rect = self._ellipse_rect
        if self._frame_rect_item is None:
            self._frame_rect_item = QGraphicsRectItem(rect)
            self._frame_rect_item.setPen(QPen(QColor(255, 210, 0, 230), 1))
            self._frame_rect_item.setBrush(QBrush(QColor(0, 0, 0, 0)))
            self._frame_rect_item.setZValue(3.0)
            self._scene.addItem(self._frame_rect_item)
        if self._frame_ellipse_item is None:
            self._frame_ellipse_item = QGraphicsEllipseItem(rect)
            self._frame_ellipse_item.setPen(QPen(QColor(0, 255, 255, 230), 1))
            self._frame_ellipse_item.setBrush(QBrush(QColor(0, 255, 255, 35)))
            self._frame_ellipse_item.setZValue(3.1)
            self._scene.addItem(self._frame_ellipse_item)
        while len(self._handle_items) < 8:
            item = QGraphicsRectItem()
            item.setPen(QPen(QColor(0, 0, 0, 220), 1))
            item.setBrush(QBrush(QColor(255, 255, 255, 230)))
            item.setZValue(3.2)
            self._scene.addItem(item)
            self._handle_items.append(item)

        self._frame_rect_item.setRect(rect)
        self._frame_ellipse_item.setRect(rect)
        size = 8.0
        half = size / 2.0
        for item, (_name, x, y) in zip(self._handle_items, self._handle_centers(rect)):
            item.setRect(QRectF(x - half, y - half, size, size))

    def _set_ellipse_frame(self, rect: QRectF) -> None:
        self._ellipse_rect = self._clamped_frame_rect(rect)
        self._sync_ellipse_frame_items()

    def has_ellipse_frame(self) -> bool:
        return self._ellipse_rect is not None

    def clear_ellipse_frame(self) -> None:
        for item in self._handle_items:
            self._scene.removeItem(item)
        self._handle_items = []
        if self._frame_ellipse_item is not None:
            self._scene.removeItem(self._frame_ellipse_item)
            self._frame_ellipse_item = None
        if self._frame_rect_item is not None:
            self._scene.removeItem(self._frame_rect_item)
            self._frame_rect_item = None
        self._ellipse_rect = None
        self._drawing_ellipse = False
        self._ellipse_start = None
        self._ellipse_drag_mode = None
        self._ellipse_drag_handle = None
        self._ellipse_drag_last = None

    def apply_ellipse_frame(self) -> None:
        if self._ellipse_rect is None:
            return
        rect = self._ellipse_rect
        self._editor.paint_ellipse(
            (
                int(rect.left()),
                int(rect.top()),
                int(rect.right()),
                int(rect.bottom()),
            )
        )
        self.clear_ellipse_frame()
        self._refresh_overlay()
        self.maskEdited.emit()

    def _hit_handle(self, pos: tuple[int, int]) -> Optional[str]:
        if self._ellipse_rect is None:
            return None
        x, y = pos
        for name, item in zip(
            [name for name, _x, _y in self._handle_centers(self._ellipse_rect)],
            self._handle_items,
        ):
            if item.rect().contains(QPointF(x, y)):
                return name
        return None

    def _begin_stroke(self, pos: object) -> None:
        if self._tool == "ellipse":
            img_pos = self._map_to_image(pos)
            if img_pos is None:
                return
            if self._ellipse_rect is not None:
                handle = self._hit_handle(img_pos)
                if handle is not None:
                    self._ellipse_drag_mode = "resize"
                    self._ellipse_drag_handle = handle
                    self._ellipse_drag_last = img_pos
                    return
                if self._ellipse_rect.contains(QPointF(img_pos[0], img_pos[1])):
                    self._ellipse_drag_mode = "move"
                    self._ellipse_drag_last = img_pos
                    return

            self._drawing_ellipse = True
            self._ellipse_start = img_pos
            if self._ellipse_start is not None:
                x, y = self._ellipse_start
                self._set_ellipse_frame(QRectF(x, y, 1, 1))
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
            cur = self._map_to_image_clamped(pos)
            if cur is None or self._ellipse_start is None:
                return
            x0, y0 = self._ellipse_start
            x1, y1 = cur
            self._set_ellipse_frame(QRectF(x0, y0, x1 - x0, y1 - y0))
            return

        if self._ellipse_drag_mode is not None and self._ellipse_rect is not None:
            cur = self._map_to_image_clamped(pos)
            if cur is None or self._ellipse_drag_last is None:
                return
            rect = self._ellipse_rect
            if self._ellipse_drag_mode == "move":
                dx = cur[0] - self._ellipse_drag_last[0]
                dy = cur[1] - self._ellipse_drag_last[1]
                dx = max(-int(rect.left()), min(dx, self._editor.width - 1 - int(rect.right())))
                dy = max(-int(rect.top()), min(dy, self._editor.height - 1 - int(rect.bottom())))
                self._set_ellipse_frame(rect.translated(dx, dy))
                self._ellipse_drag_last = cur
                return
            if self._ellipse_drag_mode == "resize" and self._ellipse_drag_handle is not None:
                left = rect.left()
                right = rect.right()
                top = rect.top()
                bottom = rect.bottom()
                handle = self._ellipse_drag_handle
                if "w" in handle:
                    left = cur[0]
                if "e" in handle:
                    right = cur[0]
                if "n" in handle:
                    top = cur[1]
                if "s" in handle:
                    bottom = cur[1]
                self._set_ellipse_frame(QRectF(left, top, right - left, bottom - top))
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
            self._ellipse_start = None
            return

        if self._ellipse_drag_mode is not None:
            self._ellipse_drag_mode = None
            self._ellipse_drag_handle = None
            self._ellipse_drag_last = None
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
        self.setFocus(Qt.FocusReason.MouseFocusReason)
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
        if self._painting or self._drawing_ellipse or self._ellipse_drag_mode is not None:
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
            if self._painting or self._drawing_ellipse or self._ellipse_drag_mode is not None:
                self._end_stroke()
                event.accept()
                return
            self._panning = False
            self._pan_last = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._ellipse_rect is not None and self._handle_frame_key(event):
            event.accept()
            return
        super().keyPressEvent(event)

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.ShortcutOverride and self._ellipse_rect is not None:
            key = getattr(event, "key", lambda: None)()
            if key in (
                Qt.Key.Key_Left,
                Qt.Key.Key_Right,
                Qt.Key.Key_Up,
                Qt.Key.Key_Down,
                Qt.Key.Key_Escape,
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
            ):
                event.accept()
                return True
        return super().event(event)

    def _handle_frame_key(self, event: QKeyEvent) -> bool:
        if self._ellipse_rect is None:
            return False
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.clear_ellipse_frame()
            return True
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.apply_ellipse_frame()
            return True
        if key not in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
        ):
            return False

        rect = self._ellipse_rect
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            left = rect.left()
            top = rect.top()
            right = rect.right()
            bottom = rect.bottom()
            if key == Qt.Key.Key_Left:
                right = max(left + 1.0, right - 1.0)
            elif key == Qt.Key.Key_Right:
                right = min(float(self._editor.width - 1), right + 1.0)
            elif key == Qt.Key.Key_Up:
                bottom = max(top + 1.0, bottom - 1.0)
            elif key == Qt.Key.Key_Down:
                bottom = min(float(self._editor.height - 1), bottom + 1.0)
            self._set_ellipse_frame(QRectF(left, top, right - left, bottom - top))
            return True

        dx = 0
        dy = 0
        if key == Qt.Key.Key_Left:
            dx = -1
        elif key == Qt.Key.Key_Right:
            dx = 1
        elif key == Qt.Key.Key_Up:
            dy = -1
        elif key == Qt.Key.Key_Down:
            dy = 1
        dx = max(-int(rect.left()), min(dx, self._editor.width - 1 - int(rect.right())))
        dy = max(-int(rect.top()), min(dy, self._editor.height - 1 - int(rect.bottom())))
        self._set_ellipse_frame(rect.translated(dx, dy))
        return True

    def refresh(self) -> None:
        self._refresh_overlay()
