from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from mcs_trainer import __version__
from mcs_trainer.ml.model_registry import build_model_metadata, normalize_model_metadata


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def package_model(
    onnx_path: Path,
    run_dir: Path,
    out_dir: Path,
    metadata: dict | None = None,
) -> Path:
    onnx_path = Path(onnx_path).resolve()
    run_dir = Path(run_dir).resolve()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_meta_path = run_dir / "run.json"
    run_meta = {}
    if run_meta_path.exists():
        run_meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
    profile = run_meta.get("profile", "general")

    staging = out_dir / ".staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    onnx_copy = staging / "coin-segmentation.onnx"
    shutil.copy2(onnx_path, onnx_copy)

    if metadata is None:
        model_json = build_model_metadata(
            model_id=f"coin-segmentation-{profile}",
            display_name=f"Coin Segmentation ({profile})",
            profile=profile,
            version=__version__,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    else:
        model_json = normalize_model_metadata(metadata, profile=profile)
    (staging / "model.json").write_text(json.dumps(model_json, indent=2), encoding="utf-8")

    metrics_src = run_dir / "metrics.json"
    if metrics_src.exists():
        shutil.copy2(metrics_src, staging / "metrics.json")

    preprocessing = {
        "resize": {
            "target": [512, 512],
            "mode": "letterbox",
            "longestMaxSize": 512,
            "padTo": [512, 512],
            "letterbox": True,
            "padValue": 0,
            "maskPadValue": 0,
        },
        "colorOrder": "RGB",
        "normalization": {"method": "divide", "value": 255.0, "range": [0.0, 1.0]},
        "maskThreshold": 0.5,
    }
    (staging / "preprocessing.json").write_text(
        json.dumps(preprocessing, indent=2), encoding="utf-8"
    )

    readme = """# MCS Coin-Segmentation Model

ONNX-Modell fuer Muenz-Segmentierung (MagicCoinSnapper PWA).

## Einsatz
- Input: float32[1,3,512,512], RGB, 0..1 (Teilung durch 255).
- Output: float32[1,1,512,512], Wahrscheinlichkeit 0..1.
- Threshold: 0.5.
- Resize: Letterbox mit LongestMaxSize 512 und Padding auf 512x512.
- Padding: Bild 0 (schwarz), Maske 0.
"""
    (staging / "README.md").write_text(readme, encoding="utf-8")

    entries = ["coin-segmentation.onnx", "model.json", "preprocessing.json", "README.md"]
    if (staging / "metrics.json").exists():
        entries.append("metrics.json")

    lines = []
    for name in entries:
        fp = staging / name
        lines.append(f"{_sha256(fp)}  {name}")
    (staging / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    zip_name = f"mcs-model-{model_json['id']}-{model_json['version']}.zip"
    zip_path = out_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in entries + ["SHA256SUMS.txt"]:
            zf.write(staging / name, name)

    shutil.rmtree(staging)
    return zip_path
