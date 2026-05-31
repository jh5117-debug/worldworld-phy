from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any
from types import SimpleNamespace

import numpy as np

from cam_physgeo.utils.io import write_json
from cam_physgeo.utils.video import read_video_frames


FLOW_PATTERNS = ("raft", "gmflow", "waft", "flow")
RAFT_WEIGHT_TERMS = ("raft-small", "raft-sintel", "raft-kitti", "raft-things", "raft-chairs")


class _RAFTArgs(SimpleNamespace):
    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and hasattr(self, key)


def inspect_flow_backend(weights_root: str | Path = "local_assets/weights/optical_flow") -> dict[str, Any]:
    root = Path(weights_root)
    files = [p for p in root.rglob("*") if p.is_file()] if root.exists() else []
    candidates = [p for p in files if any(term in p.name.lower() for term in FLOW_PATTERNS)]
    raft_files = [p for p in files if "raft" in str(p).lower() and p.suffix.lower() in {".pth", ".pt"}]
    preferred = sorted(
        raft_files,
        key=lambda p: next((i for i, term in enumerate(RAFT_WEIGHT_TERMS) if term in p.name.lower()), len(RAFT_WEIGHT_TERMS)),
    )
    return {
        "root": str(root),
        "exists": root.exists(),
        "file_count": len(files),
        "candidate_files": [str(p) for p in candidates[:50]],
        "raft_checkpoint": str(preferred[0]) if preferred else None,
        "raft_checkpoint_candidates": [str(p) for p in preferred[:10]],
        "size_bytes": sum(p.stat().st_size for p in files if p.exists()),
        "real_forward_available": bool(preferred),
        "backend": "missing" if not candidates else ("raft" if preferred else "fallback"),
        "reason": "RAFT checkpoint candidate found; smoke will attempt real RAFT forward."
        if preferred
        else (
            "No RAFT/GMFlow/WAFT loader is wired; Farneback low-res proxy is available for smoke only."
            if candidates
            else "No optical-flow checkpoint candidate found."
        ),
    }


def _load_frames(video_or_frames: str | Path | list[np.ndarray], resolution: tuple[int, int], max_frames: int) -> list[np.ndarray]:
    if isinstance(video_or_frames, (str, Path)):
        return read_video_frames(video_or_frames, max_frames=max_frames, size=(resolution[1], resolution[0]))
    return list(video_or_frames[:max_frames])


def _estimate_farneback(frames: list[np.ndarray]) -> dict[str, Any]:
    """Cheap optical-flow smoke using OpenCV Farneback.

    This is not a learned RAFT/GMFlow backend. It returns backend="fallback" so
    reward aggregation cannot treat it as a high-confidence real signal.
    """

    try:
        import cv2  # type: ignore
    except Exception as exc:
        return {"available": False, "backend": "missing", "reason": f"cv2 unavailable: {exc!r}"}
    if len(frames) < 2:
        return {"available": False, "backend": "missing", "reason": "need at least two frames"}
    flows = []
    start = time.time()
    for a, b in zip(frames[:-1], frames[1:]):
        g0 = cv2.cvtColor(np.asarray(a), cv2.COLOR_RGB2GRAY)
        g1 = cv2.cvtColor(np.asarray(b), cv2.COLOR_RGB2GRAY)
        flow = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 2, 15, 2, 5, 1.1, 0)
        flows.append(flow.astype(np.float32))
    arr = np.stack(flows)
    mag = np.linalg.norm(arr, axis=-1)
    return {
        "available": True,
        "backend": "fallback",
        "method": "opencv_farneback_lowres",
        "flow_shape": list(arr.shape),
        "mean_magnitude": float(mag.mean()),
        "max_magnitude": float(mag.max()),
        "elapsed_sec": time.time() - start,
        "confidence": 0.25,
    }


def _estimate_raft(frames: list[np.ndarray], checkpoint: str | Path, *, device: str = "cuda") -> dict[str, Any]:
    """Attempt a real RAFT forward from the local copied RAFT repo.

    This intentionally avoids downloads. Any import/model/load failure is
    returned to the caller so the CLI can report the fallback reason.
    """

    if len(frames) < 2:
        return {"available": False, "backend": "missing", "reason": "need at least two frames"}
    start = time.time()
    try:
        import sys
        import torch  # type: ignore

        checkpoint = Path(checkpoint)
        raft_root = checkpoint
        for parent in checkpoint.parents:
            if (parent / "core" / "raft.py").exists():
                raft_root = parent
                break
        for import_root in [raft_root, raft_root / "core"]:
            if str(import_root) not in sys.path:
                sys.path.insert(0, str(import_root))
        from core.raft import RAFT  # type: ignore
        from core.utils.utils import InputPadder  # type: ignore

        dev = torch.device("cuda" if device == "cuda" and torch.cuda.is_available() else "cpu")
        args = _RAFTArgs(
            small="small" in checkpoint.name.lower(),
            mixed_precision=False,
            alternate_corr=False,
            dropout=0.0,
        )
        model = RAFT(args)
        state = torch.load(checkpoint, map_location="cpu")
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        try:
            model.load_state_dict(state, strict=False)
        except RuntimeError:
            prefixed = {k.replace("module.", "", 1): v for k, v in state.items()} if isinstance(state, dict) else state
            model.load_state_dict(prefixed, strict=False)
        model = model.to(dev).eval()

        def to_tensor(frame: np.ndarray):
            arr = np.asarray(frame, dtype=np.uint8)
            return torch.from_numpy(arr).permute(2, 0, 1).float()[None].to(dev)

        flows = []
        with torch.no_grad():
            for a, b in zip(frames[:-1], frames[1:]):
                image1 = to_tensor(a)
                image2 = to_tensor(b)
                padder = InputPadder(image1.shape)
                image1, image2 = padder.pad(image1, image2)
                _, flow_up = model(image1, image2, iters=8, test_mode=True)
                flow = padder.unpad(flow_up[0]).permute(1, 2, 0).detach().float().cpu().numpy()
                flows.append(flow.astype(np.float32))
        arr = np.stack(flows)
        mag = np.linalg.norm(arr, axis=-1)
        max_mem = None
        if dev.type == "cuda":
            max_mem = int(torch.cuda.max_memory_allocated(dev))
        return {
            "available": True,
            "backend": "real",
            "method": "raft",
            "checkpoint": str(checkpoint),
            "flow_shape": list(arr.shape),
            "mean_magnitude": float(mag.mean()),
            "std_magnitude": float(mag.std()),
            "max_magnitude": float(mag.max()),
            "elapsed_sec": time.time() - start,
            "confidence": 1.0,
            "cuda_max_memory_allocated_bytes": max_mem,
        }
    except Exception as exc:
        return {
            "available": False,
            "backend": "missing",
            "method": "raft",
            "checkpoint": str(checkpoint),
            "reason": repr(exc),
            "elapsed_sec": time.time() - start,
        }


def estimate_flow(
    video_or_frames: str | Path | list[np.ndarray],
    *,
    resolution: tuple[int, int] = (256, 448),
    max_frames: int = 4,
    backend: str = "auto",
    weights_root: str | Path = "local_assets/weights/optical_flow",
    device: str = "cpu",
) -> dict[str, Any]:
    frames = _load_frames(video_or_frames, resolution, max_frames)
    backend = str(backend).lower()
    inspect = inspect_flow_backend(weights_root)
    if backend in {"auto", "raft"} and inspect.get("raft_checkpoint"):
        raft = _estimate_raft(frames, inspect["raft_checkpoint"], device=device)
        if raft.get("available"):
            return raft
        if backend == "raft":
            return raft
        fallback = _estimate_farneback(frames)
        fallback["fallback_reason"] = raft.get("reason") or "RAFT forward failed"
        fallback["attempted_backend"] = "raft"
        fallback["attempted_checkpoint"] = inspect.get("raft_checkpoint")
        return fallback
    if backend in {"gmflow", "waft"}:
        fallback = _estimate_farneback(frames)
        fallback["fallback_reason"] = f"{backend} loader is not wired and no download is allowed"
        fallback["attempted_backend"] = backend
        return fallback
    return _estimate_farneback(frames)


def _first_video_from_input(path: Path) -> Path | None:
    if path.is_file():
        return path
    if not path.exists():
        return None
    for name in ["target.mp4", "generated.mp4"]:
        found = sorted(path.rglob(name))
        if found:
            return found[0]
    videos = sorted(path.rglob("*.mp4"))
    return videos[0] if videos else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--resolution", default="256x448")
    ap.add_argument("--weights_root", default="local_assets/weights/optical_flow")
    ap.add_argument("--backend", default="auto", choices=["auto", "raft", "gmflow", "waft", "farneback"])
    args = ap.parse_args(argv)

    h, w = [int(x) for x in args.resolution.lower().split("x", 1)]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    video = _first_video_from_input(Path(args.input))
    inspect = inspect_flow_backend(args.weights_root)
    flow = estimate_flow(video, resolution=(h, w), max_frames=max(2, args.limit + 1), backend=args.backend, weights_root=args.weights_root, device=args.device) if video else {"available": False, "backend": "missing", "reason": "no input video found"}
    payload = {"device_requested": args.device, "input_video": str(video) if video else None, "checkpoint_status": inspect, "flow_smoke": flow}
    write_json(payload, out / "summary.json")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
