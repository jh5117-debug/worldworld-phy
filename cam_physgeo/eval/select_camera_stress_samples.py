from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from cam_physgeo.utils.io import write_json


MOTION_PRIORITY = {
    "relative_yaw_180_reobserve": 10,
    "lookaway": 9,
    "offscreen": 8,
    "orbit": 7,
    "strafe": 6,
    "unknown": 1,
    "static": 0,
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _rotation_angle(rot_a: np.ndarray, rot_b: np.ndarray) -> float:
    rel = rot_b @ rot_a.T
    trace = float(np.trace(rel))
    cos = max(-1.0, min(1.0, (trace - 1.0) / 2.0))
    return float(np.arccos(cos))


def pose_stats(poses: np.ndarray) -> dict[str, float]:
    arr = np.asarray(poses, dtype=np.float64)
    if arr.ndim != 3 or arr.shape[-2:] != (4, 4) or len(arr) < 2:
        return {
            "translation_magnitude": 0.0,
            "trajectory_length": 0.0,
            "rotation_magnitude_rad": 0.0,
            "yaw_proxy_rad": 0.0,
        }
    xyz = arr[:, :3, 3]
    steps = np.linalg.norm(np.diff(xyz, axis=0), axis=1)
    translation = float(np.linalg.norm(xyz[-1] - xyz[0]))
    trajectory = float(np.sum(steps))
    rotations = [_rotation_angle(arr[i, :3, :3], arr[i + 1, :3, :3]) for i in range(len(arr) - 1)]
    total_rot = float(np.sum(rotations))
    forward = arr[:, :3, 2]
    yaw = np.unwrap(np.arctan2(forward[:, 0], forward[:, 2]))
    yaw_proxy = float(np.max(yaw) - np.min(yaw)) if len(yaw) else 0.0
    return {
        "translation_magnitude": translation,
        "trajectory_length": trajectory,
        "rotation_magnitude_rad": total_rot,
        "yaw_proxy_rad": abs(yaw_proxy),
    }


def score_row(row: dict[str, Any]) -> float:
    motion = str(row.get("camera_motion") or "unknown")
    priority = MOTION_PRIORITY.get(motion, 2 if motion != "static" else 0)
    return (
        float(priority) * 10.0
        + float(row.get("trajectory_length") or 0.0) * 3.0
        + float(row.get("translation_magnitude") or 0.0) * 4.0
        + float(row.get("rotation_magnitude_rad") or 0.0) * 2.0
        + float(row.get("yaw_proxy_rad") or 0.0) * 2.0
    )


def scan_samples(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sample_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        pose_path = sample_dir / "poses.npy"
        if not pose_path.exists():
            continue
        meta = _read_json(sample_dir / "metadata.json")
        try:
            stats = pose_stats(np.load(pose_path))
            row = {
                "sample_id": sample_dir.name,
                "sample_dir": str(sample_dir),
                "camera_motion": meta.get("camera_motion", "unknown"),
                "template": meta.get("template", "unknown"),
                **stats,
            }
            row["stress_score"] = score_row(row)
            rows.append(row)
        except Exception as exc:
            rows.append(
                {
                    "sample_id": sample_dir.name,
                    "sample_dir": str(sample_dir),
                    "camera_motion": meta.get("camera_motion", "unknown"),
                    "template": meta.get("template", "unknown"),
                    "error": repr(exc),
                    "stress_score": -1.0,
                }
            )
    return sorted(rows, key=lambda r: float(r.get("stress_score") or -1.0), reverse=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top_k", type=int, default=10)
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = scan_samples(Path(args.samples))
    top = rows[: args.top_k]
    write_json({"top_k": args.top_k, "rows": top, "all_count": len(rows)}, out / "summary.json")
    if top:
        (out / "top_sample.txt").write_text(str(top[0]["sample_id"]) + "\n", encoding="utf-8")
    with (out / "top_samples.csv").open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "sample_id",
            "camera_motion",
            "template",
            "stress_score",
            "translation_magnitude",
            "trajectory_length",
            "rotation_magnitude_rad",
            "yaw_proxy_rad",
            "sample_dir",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in top:
            writer.writerow({k: row.get(k) for k in fieldnames})
    print(json.dumps({"top_sample": top[0] if top else None, "out": str(out), "count": len(rows)}, indent=2, sort_keys=True))
    return 0 if top else 2


if __name__ == "__main__":
    raise SystemExit(main())
