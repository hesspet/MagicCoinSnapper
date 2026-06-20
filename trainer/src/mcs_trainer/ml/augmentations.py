from __future__ import annotations

import albumentations as A


def get_train_transforms() -> A.Compose:
    return A.Compose(
        [
            A.Resize(512, 512),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.RandomBrightnessContrast(
                brightness_limit=0.1, contrast_limit=0.1, p=0.3
            ),
            A.Rotate(limit=15, p=0.3),
        ]
    )


def get_val_transforms() -> A.Compose:
    return A.Compose([A.Resize(512, 512)])
