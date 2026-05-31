from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from cam_physgeo.utils.io import write_json
from cam_physgeo.utils.video import read_video_frames


FLOW_PATTERNS = ("raft", "gmflow", "waft", "flow")


def inspect_flow_backend(weights_root: str | Path = "local_assets/weights/optical_flow") -> dict[str, Any]:
    root = Path(weights_root)
    files = [p for p in root.rglob("*") if p.is_file()] if root.exists() else []
    candidates = [p for p in files if any(term in p.name.lower() for term in FLOW_PATTERNS)]
    return {
        "root": str(root),
        "exists": root.exists(),
        "file_count": len(files),
        "candidate_files": [str(p) for p in candidates[:50]],
        "size_bytes": sum(p.stat().st_size for p in files if p.exists()),
        "real_forward_available": False,
        "backend": "missing" if not candidates else "fallback",
        "reason": "No RAFT/GMFlow/WAFT loader is wired; Farneback low-res proxy is available for smoke only."
        if candidates
        else "No optical-flow checkpoint candidate found.",
    }


def estimate_flow(video_or_frames: str | Path | list[np.ndarray], *, resolution: tuple[int, int] = (256, 448), max_frames: int = 4) -> dict[str, Any]:
    """Cheap optical-flow smoke using OpenCV Farneback.

    This is not a learned RAFT/GMFlow backend. It returns backend="fallback" so
    reward aggregation cannot treat it as a high-confidence real signal.
    """

    try:
        import cv2  # type: ignore
    except Exception as exc:
        return {"available": False, "backend": "missing", "reason": f"cv2 unavailable: {exc!r}"}
    if isinstance(video_or_frames, (str, Path)):
        frames = read_video_frames(video_or_frames, max_frames=max_frames, size=(resolution[1], resolution[0]))
    else:
        frames = video_or_frames[:max_frames]
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
    args = ap.parse_args(argv)

    h, w = [int(x) for x in args.resolution.lower().split("x", 1)]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    video = _first_video_from_input(Path(args.input))
    inspect = inspect_flow_backend(args.weights_root)
    flow = estimate_flow(video, resolution=(h, w), max_frames=max(2, args.limit + 1)) if video else {"available": False, "backend": "missing", "reason": "no input video found"}
    payload = {"device_requested": args.device, "input_video": str(video) if video else None, "checkpoint_status": inspect, "flow_smoke": flow}
    write_json(payload, out / "summary.json")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
