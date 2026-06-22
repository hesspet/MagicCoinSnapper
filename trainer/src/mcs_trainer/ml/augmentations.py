from __future__ import annotations

import inspect

import albumentations as A
import cv2


def _constant_border_kwargs(transform_cls: type) -> dict:
    params = inspect.signature(transform_cls).parameters
    kwargs = {"border_mode": cv2.BORDER_CONSTANT}
    if "fill" in params:
        kwargs.update({"fill": 0, "fill_mask": 0})
    else:
        kwargs.update({"value": 0, "mask_value": 0})
    return kwargs


def _coarse_dropout_kwargs() -> dict:
    params = inspect.signature(A.CoarseDropout).parameters
    if "num_holes_range" in params:
        return {
            "num_holes_range": (1, 5),
            "hole_height_range": (8, 48),
            "hole_width_range": (8, 96),
            "fill": 0,
            "fill_mask": None,
        }
    return {
        "max_holes": 5,
        "max_height": 48,
        "max_width": 96,
        "min_holes": 1,
        "min_height": 8,
        "min_width": 8,
        "fill_value": 0,
        "mask_fill_value": None,
    }


def _gauss_noise_kwargs() -> dict:
    params = inspect.signature(A.GaussNoise).parameters
    if "std_range" in params:
        return {"std_range": (0.01, 0.05), "mean_range": (0.0, 0.0)}
    return {"var_limit": (5.0, 25.0), "mean": 0.0}


def _letterbox() -> list:
    return [
        A.LongestMaxSize(
            max_size=512,
            interpolation=cv2.INTER_LINEAR,
            mask_interpolation=cv2.INTER_NEAREST,
        ),
        A.PadIfNeeded(
            min_height=512,
            min_width=512,
            **_constant_border_kwargs(A.PadIfNeeded),
        ),
    ]


def get_train_transforms() -> A.Compose:
    return A.Compose(
        _letterbox()
        + [
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.Rotate(
                limit=20,
                interpolation=cv2.INTER_LINEAR,
                mask_interpolation=cv2.INTER_NEAREST,
                p=0.35,
                **_constant_border_kwargs(A.Rotate),
            ),
            A.Perspective(
                scale=(0.02, 0.06),
                keep_size=True,
                interpolation=cv2.INTER_LINEAR,
                mask_interpolation=cv2.INTER_NEAREST,
                p=0.2,
                **_constant_border_kwargs(A.Perspective),
            ),
            A.RandomBrightnessContrast(
                brightness_limit=0.25, contrast_limit=0.25, p=0.45
            ),
            A.HueSaturationValue(
                hue_shift_limit=5, sat_shift_limit=15, val_shift_limit=15, p=0.2
            ),
            A.OneOf(
                [
                    A.GaussianBlur(blur_limit=(3, 5)),
                    A.MotionBlur(blur_limit=5),
                ],
                p=0.2,
            ),
            A.GaussNoise(p=0.2, **_gauss_noise_kwargs()),
            A.CoarseDropout(p=0.25, **_coarse_dropout_kwargs()),
        ]
    )


def get_val_transforms() -> A.Compose:
    return A.Compose(_letterbox())
