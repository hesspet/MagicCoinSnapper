from __future__ import annotations

import torch


def _binary(t: torch.Tensor, threshold: float = 0.5) -> torch.Tensor:
    return (t > threshold).float()


def dice_score(
    pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5, eps: float = 1e-7
) -> torch.Tensor:
    pred_b = _binary(pred, threshold)
    target_b = _binary(target, threshold)
    inter = (pred_b * target_b).sum(dim=(1, 2, 3))
    denom = pred_b.sum(dim=(1, 2, 3)) + target_b.sum(dim=(1, 2, 3))
    return ((2.0 * inter + eps) / (denom + eps)).mean()


def iou_score(
    pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5, eps: float = 1e-7
) -> torch.Tensor:
    pred_b = _binary(pred, threshold)
    target_b = _binary(target, threshold)
    inter = (pred_b * target_b).sum(dim=(1, 2, 3))
    union = pred_b.sum(dim=(1, 2, 3)) + target_b.sum(dim=(1, 2, 3)) - inter
    return ((inter + eps) / (union + eps)).mean()
