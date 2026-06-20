from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

from mcs_trainer.dataset.schemas import AnnotatedSample


@dataclass
class _Snapshot:
    pixels: bytes
    width: int
    height: int


class MaskEditor:
    """Verwaltet die Masken-QImage fuer das aktuelle Sample inkl. Undo/Redo."""

    def __init__(self, max_stack: int = 50) -> None:
        self._max_stack = max_stack
        self._width: int = 0
        self._height: int = 0
        self._pixels: bytearray = bytearray()
        self._undo: list[_Snapshot] = []
        self._redo: list[_Snapshot] = []
        self._sample: Optional[AnnotatedSample] = None
        self._image_path: Optional[Path] = None

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def set_sample(
        self,
        sample: AnnotatedSample,
        image_path: Path,
        existing_mask: Optional[Path] = None,
    ) -> None:
        self._sample = sample
        self._image_path = Path(image_path)
        self._reset_stack()
        with Image.open(self._image_path) as img:
            img = img.convert("RGB")
            self._width, self._height = img.size
        self._pixels = bytearray(self._width * self._height)
        if existing_mask is not None and Path(existing_mask).exists():
            try:
                with Image.open(existing_mask) as mask:
                    mask = mask.convert("L").resize((self._width, self._height))
                    data = list(mask.getdata())
                    self._pixels = bytearray(
                        255 if v >= 128 else 0 for v in data
                    )
            except Exception:
                self._pixels = bytearray(self._width * self._height)

    def _reset_stack(self) -> None:
        self._undo = []
        self._redo = []

    def _push_undo(self) -> None:
        if self._width == 0:
            return
        snap = _Snapshot(bytes(self._pixels), self._width, self._height)
        self._undo.append(snap)
        if len(self._undo) > self._max_stack:
            self._undo.pop(0)
        self._redo.clear()

    def undo(self) -> bool:
        if not self._undo:
            return False
        cur = _Snapshot(bytes(self._pixels), self._width, self._height)
        self._redo.append(cur)
        snap = self._undo.pop()
        self._pixels = bytearray(snap.pixels)
        self._width = snap.width
        self._height = snap.height
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        cur = _Snapshot(bytes(self._pixels), self._width, self._height)
        self._undo.append(cur)
        snap = self._redo.pop()
        self._pixels = bytearray(snap.pixels)
        self._width = snap.width
        self._height = snap.height
        return True

    def _index(self, x: int, y: int) -> int:
        return y * self._width + x

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self._width and 0 <= y < self._height

    def paint(self, pos: tuple[int, int], radius: int, erase: bool = False) -> None:
        if self._width == 0:
            return
        self._push_undo()
        cx, cy = pos
        r = max(1, int(radius))
        value = 0 if erase else 255
        r2 = r * r
        for y in range(max(0, cy - r), min(self._height, cy + r + 1)):
            for x in range(max(0, cx - r), min(self._width, cx + r + 1)):
                dx = x - cx
                dy = y - cy
                if dx * dx + dy * dy <= r2:
                    self._pixels[self._index(x, y)] = value

    def paint_ellipse(
        self, rect: tuple[int, int, int, int], erase: bool = False
    ) -> None:
        if self._width == 0:
            return
        self._push_undo()
        x0, y0, x1, y1 = rect
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = max(1.0, (x1 - x0) / 2.0)
        ry = max(1.0, (y1 - y0) / 2.0)
        value = 0 if erase else 255
        for y in range(max(0, int(y0)), min(self._height, int(y1) + 1)):
            for x in range(max(0, int(x0)), min(self._width, int(x1) + 1)):
                dx = (x + 0.5 - cx) / rx
                dy = (y + 0.5 - cy) / ry
                if dx * dx + dy * dy <= 1.0:
                    self._pixels[self._index(x, y)] = value

    def clear(self) -> None:
        if self._width == 0:
            return
        self._push_undo()
        self._pixels = bytearray(self._width * self._height)

    def pixels(self) -> bytes:
        return bytes(self._pixels)

    def to_mask_image(self) -> Image.Image:
        img = Image.frombytes("L", (self._width, self._height), bytes(self._pixels))
        return img

    def to_mask_png_bytes(self) -> bytes:
        img = self.to_mask_image()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
