from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from cam_physgeo.utils.video import read_video_frames


class FeatureExtractorUnavailable(RuntimeError):
    pass


class FrozenVideoFeatureExtractor:
    """Small wrapper for optional frozen feature backends.

    The real DINOv2/V-JEPA2/VideoMAE2 models are kept in ``local_assets`` and may
    be unavailable on a fresh checkout. Reward code can still call the proxy
    feature functions below, while this class records the missing backend instead
    of silently pretending a teacher model was used.
    """

    def __init__(self, name: str = "vjepa2_or_videomae_fallback", checkpoint: str | None = None):
        self.name = name
        self.checkpoint = checkpoint

    def __call__(self, video):
        raise FeatureExtractorUnavailable(
            f"{self.name} is not loaded. Configure local_assets/weights and run the backend smoke test first."
        )


def video_feature_signature(
    video_path: str | Path | None,
    *,
    max_frames: int = 12,
    size: tuple[int, int] = (96, 64),
) -> dict[str, Any]:
    """Return a deterministic lightweight video feature signature.

    This is not a replacement for DINOv2/V-JEPA2. It gives foreground/reobserve
    rewards a non-mask visual signal during smoke tests and provides a stable
    fallback when optional external checkpoints are absent.
    """

    frames = read_video_frames(video_path, max_frames=max_frames, size=size)
    if not frames:
        return {"available": False, "status": "missing_video", "feature": None}
    arr = np.asarray(frames, dtype=np.float32) / 255.0
    means = arr.mean(axis=(1, 2))
    stds = arr.std(axis=(1, 2))
    diffs = np.abs(np.diff(arr, axis=0)).mean(axis=(1, 2, 3)) if len(arr) > 1 else np.array([0.0], dtype=np.float32)
    hist_parts = []
    for channel in range(3):
        hist, _ = np.histogram(arr[..., channel], bins=16, range=(0.0, 1.0), density=True)
        hist_parts.append(hist.astype(np.float32))
    feature = np.concatenate([means.mean(axis=0), stds.mean(axis=0), np.asarray([diffs.mean(), diffs.max()]), *hist_parts])
    norm = float(np.linalg.norm(feature)) + 1e-8
    return {
        "available": True,
        "status": "proxy_color_temporal_signature",
        "feature": (feature / norm).astype(np.float32),
        "num_frames": int(len(frames)),
        "temporal_delta_mean": float(diffs.mean()),
        "temporal_delta_max": float(diffs.max()),
    }


def cosine_similarity(a: np.ndarray | None, b: np.ndarray | None) -> float | None:
    if a is None or b is None:
        return None
    a = np.asarray(a, dtype=np.float32).reshape(-1)
    b = np.asarray(b, dtype=np.float32).reshape(-1)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def first_last_feature_similarity(video_path: str | Path | None) -> dict[str, Any]:
    frames = read_video_frames(video_path, max_frames=16, size=(96, 64))
    if len(frames) < 2:
        return {"available": False, "similarity": None, "status": "missing_video"}
    first = _frame_feature(frames[0])
    last = _frame_feature(frames[-1])
    return {
        "available": True,
        "similarity": cosine_similarity(first, last),
        "status": "proxy_first_last_feature",
    }


def _frame_feature(frame: np.ndarray) -> np.ndarray:
    arr = np.asarray(frame, dtype=np.float32) / 255.0
    means = arr.mean(axis=(0, 1))
    stds = arr.std(axis=(0, 1))
    hist_parts = []
    for channel in range(3):
        hist, _ = np.histogram(arr[..., channel], bins=16, range=(0.0, 1.0), density=True)
        hist_parts.append(hist.astype(np.float32))
    vec = np.concatenate([means, stds, *hist_parts])
    return vec / (np.linalg.norm(vec) + 1e-8)


def inspect_backend(name: str, weights_root: str | Path, device: str = "cpu") -> dict[str, Any]:
    root = Path(weights_root)
    if name == "dinov2":
        candidates = [root / "dinov2", root / "DINOv2"]
    elif name in {"vjepa2_or_videomae2", "vjepa2", "videomae2"}:
        candidates = [root / "vjepa2", root / "videomae2", root / "V-JEPA2"]
    else:
        candidates = [root / name]
    existing = [p for p in candidates if p.exists()]
    files = []
    for path in existing:
        files.extend([p for p in path.rglob("*") if p.is_file()])
    result = {
        "backend": name,
        "weights_root": str(root),
        "candidate_paths": [str(p) for p in candidates],
        "found": bool(existing),
        "file_count": len(files),
        "size_bytes": sum(_safe_size(p) for p in files),
        "device_requested": device,
        "import_torch": False,
        "load_test": "fallback_proxy_only",
        "notes": [],
    }
    try:
        import torch  # type: ignore

        result["import_torch"] = True
        result["torch_version"] = getattr(torch, "__version__", "unknown")
        if device == "cuda":
            result["cuda_available"] = bool(torch.cuda.is_available())
        if files:
            result["load_test"] = "path_present_not_loaded"
            result["notes"].append("Smoke avoids loading large teacher checkpoints; adapter path is verified.")
        else:
            result["notes"].append("No local checkpoint found; reward uses proxy visual features until weights are added.")
    except Exception as exc:
        result["notes"].append(f"torch_import_failed:{exc!r}")
    dummy = np.zeros((32, 32, 3), dtype=np.uint8)
    result["proxy_feature_dim"] = int(_frame_feature(dummy).shape[0])
    return result


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", required=True, choices=["dinov2", "vjepa2_or_videomae2", "vjepa2", "videomae2"])
    ap.add_argument("--weights_root", default="local_assets/weights")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--limit", type=int, default=1)
    args = ap.parse_args(argv)
    result = inspect_backend(args.check, args.weights_root, args.device)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
