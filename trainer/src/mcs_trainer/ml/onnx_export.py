from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch

from mcs_trainer.ml.model import build_model


def export_onnx(run_dir: Path, opset: int = 17) -> Path:
    run_dir = Path(run_dir).resolve()
    ckpt_path = run_dir / "checkpoints" / "best.pt"
    if not ckpt_path.exists():
        ckpt_path = run_dir / "checkpoints" / "last.pt"
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Kein Checkpoint in {run_dir / 'checkpoints'}")

    model = build_model()
    ckpt = torch.load(ckpt_path, map_location="cpu")
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    dummy = torch.zeros(1, 3, 512, 512, dtype=torch.float32)
    onnx_path = run_dir / "coin-segmentation.onnx"
    torch.onnx.export(
        model,
        (dummy,),
        str(onnx_path),
        input_names=["input"],
        output_names=["mask"],
        opset_version=opset,
        dynamic_axes=None,
        do_constant_folding=True,
        dynamo=False,
    )

    try:
        import onnx
        import onnxsim

        model_proto = onnx.load(str(onnx_path))
        simplified, ok = onnxsim.simplify(model_proto)
        if ok:
            onnx.save(simplified, str(onnx_path))
    except Exception:
        pass

    info = validate_onnx(onnx_path)
    (run_dir / "onnx_validation.json").write_text(
        json.dumps(info, indent=2), encoding="utf-8"
    )
    return onnx_path


def validate_onnx(onnx_path: Path) -> dict:
    onnx_path = Path(onnx_path).resolve()
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    in_name = sess.get_inputs()[0].name
    out_name = sess.get_outputs()[0].name
    in_shape = [str(d) for d in sess.get_inputs()[0].shape]
    out_shape = [str(d) for d in sess.get_outputs()[0].shape]
    dummy = np.zeros(
        tuple(int(d) for d in sess.get_inputs()[0].shape), dtype=np.float32
    )
    out = sess.run([out_name], {in_name: dummy})[0]
    return {
        "path": str(onnx_path),
        "inputName": in_name,
        "outputName": out_name,
        "inputShape": in_shape,
        "outputShape": out_shape,
        "outputDtype": str(out.dtype),
        "outputMin": float(out.min()),
        "outputMax": float(out.max()),
    }
