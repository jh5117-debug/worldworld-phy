from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from cam_physgeo.trd.feature_extractors import inspect_backend
from cam_physgeo.utils.io import write_json
from cam_physgeo.utils.video import read_video_frames


DINO_MODEL_NAME = "dinov2_vits14"
DINO_URL = "https://dl.fbaipublicfiles.com/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth"
MAX_SMALL_DOWNLOAD_BYTES = 1_000_000_000


def _truthy(value: Any) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y", "on"}


def dinov2_target_dir(weights_root: str | Path) -> Path:
    return Path(weights_root) / "dinov2" / DINO_MODEL_NAME


def find_dinov2_checkpoint(weights_root: str | Path) -> Path | None:
    roots = [dinov2_target_dir(weights_root), Path(weights_root) / "dinov2", Path(weights_root) / "DINOv2"]
    patterns = ("dinov2_vits14", "vits14", "dino")
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".pth", ".pt", ".bin"}:
                if any(term in path.name.lower() for term in patterns):
                    candidates.append(path)
    if not candidates:
        return None
    return sorted(candidates, key=lambda p: (0 if "vits14" in p.name.lower() else 1, p.stat().st_size))[0]


def download_dinov2_small(weights_root: str | Path, *, model_name: str = DINO_MODEL_NAME) -> dict[str, Any]:
    if model_name != DINO_MODEL_NAME:
        return {"downloaded": False, "error": f"only {DINO_MODEL_NAME} is allowed in this task"}
    target = dinov2_target_dir(weights_root) / "dinov2_vits14_pretrain.pth"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return {"downloaded": False, "already_exists": True, "path": str(target), "size_bytes": target.stat().st_size}
    try:
        req = urllib.request.Request(DINO_URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as resp:
            size = int(resp.headers.get("Content-Length") or "0")
        if size and size > MAX_SMALL_DOWNLOAD_BYTES:
            return {"downloaded": False, "error": f"download too large: {size} bytes", "url": DINO_URL}
    except Exception as exc:
        # Some mirrors do not allow HEAD. Continue, but still enforce size after
        # download and delete the incomplete temp file on failure.
        size = 0
        head_warning = repr(exc)
    else:
        head_warning = None
    tmp = target.with_suffix(".tmp")
    start = time.time()
    try:
        urllib.request.urlretrieve(DINO_URL, tmp)
        final_size = tmp.stat().st_size
        if final_size > MAX_SMALL_DOWNLOAD_BYTES:
            tmp.unlink(missing_ok=True)
            return {"downloaded": False, "error": f"download exceeded limit: {final_size} bytes", "url": DINO_URL}
        tmp.replace(target)
        return {
            "downloaded": True,
            "path": str(target),
            "size_bytes": final_size,
            "url": DINO_URL,
            "elapsed_sec": time.time() - start,
            "head_content_length": size,
            "head_warning": head_warning,
        }
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        return {"downloaded": False, "error": repr(exc), "url": DINO_URL, "head_warning": head_warning}


@lru_cache(maxsize=2)
def _load_dinov2_cached(checkpoint: str, device: str = "cpu"):
    import torch  # type: ignore

    os.environ.setdefault("TORCH_HOME", "local_assets/cache/torch")
    # The hub repo is code only; weights are loaded from local_assets below.
    model = torch.hub.load("facebookresearch/dinov2", DINO_MODEL_NAME, pretrained=False, trust_repo=True)
    state = torch.load(checkpoint, map_location="cpu")
    if isinstance(state, dict) and "model" in state:
        state = state["model"]
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    missing, unexpected = model.load_state_dict(state, strict=False)
    dev = torch.device("cuda" if device == "cuda" and torch.cuda.is_available() else "cpu")
    model = model.to(dev).eval()
    return model, dev, list(missing), list(unexpected)


def _preprocess_frames(frames: list[np.ndarray], device: Any):
    import torch  # type: ignore
    import torch.nn.functional as F  # type: ignore

    arr = np.stack([np.asarray(f, dtype=np.float32) / 255.0 for f in frames])
    x = torch.from_numpy(arr).permute(0, 3, 1, 2)
    x = F.interpolate(x, size=(224, 224), mode="bilinear", align_corners=False)
    mean = torch.tensor([0.485, 0.456, 0.406], dtype=x.dtype).view(1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225], dtype=x.dtype).view(1, 3, 1, 1)
    x = (x - mean) / std
    return x.to(device)


def _features_from_model(model: Any, batch: Any):
    import torch  # type: ignore

    with torch.no_grad():
        if hasattr(model, "forward_features"):
            out = model.forward_features(batch)
            if isinstance(out, dict):
                if "x_norm_patchtokens" in out:
                    patch = out["x_norm_patchtokens"]
                    return patch.mean(dim=1)
                if "x_norm_clstoken" in out:
                    return out["x_norm_clstoken"]
        out = model(batch)
        if isinstance(out, (tuple, list)):
            out = out[0]
        return out


def estimate_dino_video_features(
    video_or_frames: str | Path | list[np.ndarray] | None,
    *,
    weights_root: str | Path = "local_assets/weights",
    device: str = "cpu",
    allow_download_small: bool = False,
    model_name: str = DINO_MODEL_NAME,
    max_frames: int = 4,
    allow_dummy: bool = False,
) -> dict[str, Any]:
    start = time.time()
    checkpoint = find_dinov2_checkpoint(weights_root)
    download_info = None
    if checkpoint is None and allow_download_small:
        download_info = download_dinov2_small(weights_root, model_name=model_name)
        checkpoint = find_dinov2_checkpoint(weights_root)
    if checkpoint is None:
        return {
            "available": False,
            "backend": "missing",
            "method": "dinov2",
            "reason": "no local dinov2_vits14 checkpoint",
            "download": download_info,
            "target_path": str(dinov2_target_dir(weights_root)),
        }
    if isinstance(video_or_frames, (str, Path)):
        frames = read_video_frames(video_or_frames, max_frames=max_frames, size=(224, 224))
    elif video_or_frames is None:
        if not allow_dummy:
            return {"available": False, "backend": "missing", "method": "dinov2", "reason": "no input video", "checkpoint": str(checkpoint)}
        frames = [np.zeros((224, 224, 3), dtype=np.uint8)]
    else:
        frames = list(video_or_frames[:max_frames])
    if not frames:
        return {"available": False, "backend": "missing", "method": "dinov2", "reason": "no frames", "checkpoint": str(checkpoint)}
    try:
        import torch  # type: ignore

        model, dev, missing, unexpected = _load_dinov2_cached(str(checkpoint), device)
        batch = _preprocess_frames(frames, dev)
        feats = _features_from_model(model, batch).detach().float().cpu().numpy()
        if feats.ndim == 1:
            feats = feats[None]
        norms = np.linalg.norm(feats, axis=1, keepdims=True) + 1e-8
        feats = feats / norms
        first_last = None
        if len(feats) >= 2:
            first_last = float(np.sum(feats[0] * feats[-1]))
        max_mem = None
        if dev.type == "cuda":
            max_mem = int(torch.cuda.max_memory_allocated(dev))
        return {
            "available": True,
            "backend": "real",
            "method": "dinov2",
            "model_name": model_name,
            "checkpoint": str(checkpoint),
            "feature_shape": list(feats.shape),
            "first_last_similarity": first_last,
            "num_frames": len(frames),
            "elapsed_sec": time.time() - start,
            "cuda_max_memory_allocated_bytes": max_mem,
            "missing_keys_count": len(missing),
            "unexpected_keys_count": len(unexpected),
            "download": download_info,
        }
    except Exception as exc:
        return {
            "available": False,
            "backend": "missing",
            "method": "dinov2",
            "checkpoint": str(checkpoint),
            "reason": repr(exc),
            "download": download_info,
            "elapsed_sec": time.time() - start,
        }


def dinov2_plan(weights_root: str | Path = "local_assets/weights") -> dict[str, Any]:
    status = inspect_backend("dinov2", weights_root, "cpu")
    root = dinov2_target_dir(weights_root)
    return {
        "status": status,
        "recommended_model": DINO_MODEL_NAME,
        "target_path": str(root),
        "estimated_size": "about 80-100 MB for the pretrain checkpoint",
        "requires_hf_token": False,
        "requires_user_approval": False,
        "auto_download_performed": False,
        "download_command_draft": (
            "mkdir -p local_assets/weights/dinov2/dinov2_vits14 && "
            f"curl -L {DINO_URL} -o local_assets/weights/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth"
        ),
        "reward_uses": ["R_fg foreground identity", "R_reobs object/background feature similarity", "GeoFlow-style R_dino"],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", required=True, choices=["dinov2"])
    ap.add_argument("--weights_root", default="local_assets/weights")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--allow_download_small", default="false")
    ap.add_argument("--model_name", default=DINO_MODEL_NAME)
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    status = inspect_backend(args.check, args.weights_root, args.device)
    checkpoint_before = find_dinov2_checkpoint(args.weights_root)
    result = estimate_dino_video_features(
        None,
        weights_root=args.weights_root,
        device=args.device,
        allow_download_small=_truthy(args.allow_download_small),
        model_name=args.model_name,
        max_frames=max(1, args.limit),
        allow_dummy=True,
    )
    checkpoint_after = find_dinov2_checkpoint(args.weights_root)
    payload = {
        "check": args.check,
        "backend_status": status,
        "checkpoint_before": str(checkpoint_before) if checkpoint_before else None,
        "checkpoint_after": str(checkpoint_after) if checkpoint_after else None,
        "can_forward": bool(result.get("available") and result.get("backend") == "real"),
        "feature_shape": result.get("feature_shape"),
        "forward": result,
        "plan": dinov2_plan(args.weights_root),
        "local_checkpoint_present": checkpoint_after is not None,
        "R_fg_R_reobs_dpo_ready": bool(result.get("available") and result.get("backend") == "real"),
    }
    write_json(payload, out / "summary.json")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["can_forward"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
