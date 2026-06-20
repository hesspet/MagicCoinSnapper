from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from mcs_trainer.dataset.schemas import AnnotatedMetadata
from mcs_trainer.ml.augmentations import get_train_transforms, get_val_transforms


class CoinSegDataset(Dataset):
    def __init__(
        self,
        metadata: AnnotatedMetadata,
        dataset_dir: Path,
        sample_ids: list[str],
        train: bool = True,
    ) -> None:
        self.dataset_dir = Path(dataset_dir)
        self.transform = get_train_transforms() if train else get_val_transforms()
        by_id = {s.id: s for s in metadata.samples}
        self.samples = [
            by_id[sid]
            for sid in sample_ids
            if sid in by_id and not by_id[sid].excluded
        ]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        sample = self.samples[idx]
        image_path = self.dataset_dir / sample.image
        mask_path = self.dataset_dir / sample.mask
        if not mask_path.exists():
            raise FileNotFoundError(f"Maske fehlt: {mask_path}")
        image = np.array(Image.open(image_path).convert("RGB"))
        mask = np.array(Image.open(mask_path).convert("L"))
        augmented = self.transform(image=image, mask=mask)
        img = augmented["image"].astype(np.float32) / 255.0
        msk = augmented["mask"].astype(np.float32) / 255.0
        if msk.ndim == 2:
            msk = msk[:, :, None]
        img_tensor = torch.from_numpy(np.transpose(img, (2, 0, 1))).contiguous()
        mask_tensor = torch.from_numpy(np.transpose(msk, (2, 0, 1))).contiguous()
        return img_tensor, mask_tensor
