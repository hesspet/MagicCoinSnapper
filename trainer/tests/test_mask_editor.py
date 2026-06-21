from __future__ import annotations

from pathlib import Path

from PIL import Image

from mcs_trainer.app.mask_editor import MaskEditor
from mcs_trainer.dataset.schemas import AnnotatedSample


def test_paint_ellipse_fills_and_erases(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (7, 7), (10, 20, 30)).save(image_path)
    sample = AnnotatedSample(
        id="s1",
        image="sample.png",
        mask="mask.png",
        width=7,
        height=7,
        contentType="image/png",
    )
    editor = MaskEditor()
    editor.set_sample(sample, image_path)

    editor.paint_ellipse((1, 1, 5, 5))

    pixels = editor.pixels()
    assert pixels[3 * 7 + 3] == 255
    assert pixels[0] == 0

    editor.paint_ellipse((1, 1, 5, 5), erase=True)

    assert editor.pixels()[3 * 7 + 3] == 0
