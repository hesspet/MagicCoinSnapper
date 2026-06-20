from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from mcs_trainer import __version__


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def package_model(onnx_path: Path, run_dir: Path, out_dir: Path) -> Path:
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

    model_json = {
        "profile": profile,
        "version": __version__,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "input": {
            "name": "input",
            "dtype": "float32",
            "shape": [1, 3, 512, 512],
            "layout": "NCHW",
            "colorOrder": "RGB",
            "normalization": "/255",
            "range": [0.0, 1.0],
        },
        "output": {
            "name": "mask",
            "dtype": "float32",
            "shape": [1, 1, 512, 512],
            "range": [0.0, 1.0],
            "threshold": 0.5,
        },
    }
    (staging / "model.json").write_text(json.dumps(model_json, indent=2), encoding="utf-8")

    metrics_src = run_dir / "metrics.json"
    if metrics_src.exists():
        shutil.copy2(metrics_src, staging / "metrics.json")

    preprocessing = {
        "resize": {"target": [512, 512], "mode": "direct-stretch", "letterbox": False},
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
- Resize: direkt auf 512x512 (kein Letterboxing).
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

    zip_name = f"mcs-model-{profile}-{__version__}.zip"
    zip_path = out_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in entries + ["SHA256SUMS.txt"]:
            zf.write(staging / name, name)

    shutil.rmtree(staging)
    return zip_path
