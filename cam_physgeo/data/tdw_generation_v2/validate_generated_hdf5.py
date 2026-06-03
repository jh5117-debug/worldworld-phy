from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import h5py  # type: ignore
except Exception:  # pragma: no cover
    h5py = None


def _visit_keys(h5) -> set[str]:
    keys: set[str] = set()
    def visitor(name, obj):
        keys.add(name)
    h5.visititems(visitor)
    return keys


def validate_hdf5(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}
    if h5py is None:
        info.update({"status": "blocked", "error": "h5py unavailable"})
        return info
    if not path.exists():
        info.update({"status": "missing"})
        return info
    try:
        with h5py.File(path, "r") as f:
            keys = _visit_keys(f)
            frame_keys = sorted(f["frames"].keys()) if "frames" in f else []
            first = f"frames/{frame_keys[0]}/images" if frame_keys else ""
            passes = sorted(f[first].keys()) if first and first in f else []
            label_counts = {"camera_pose": 0, "camera_position": 0, "camera_aim": 0}
            for frame in frame_keys:
                labels = f.get(f"frames/{frame}/labels")
                if labels is not None:
                    for k in label_counts:
                        if k in labels:
                            label_counts[k] += 1
            info.update({
                "status": "ok",
                "frame_count": len(frame_keys),
                "passes": passes,
                "has_rgb": "_img" in passes,
                "has_depth": "_depth" in passes,
                "has_id": "_id" in passes,
                "has_camera_pose": label_counts["camera_pose"] == len(frame_keys) and len(frame_keys) > 0,
                "has_camera_position": label_counts["camera_position"] == len(frame_keys) and len(frame_keys) > 0,
                "has_camera_aim": label_counts["camera_aim"] == len(frame_keys) and len(frame_keys) > 0,
                "has_projection_or_camera_matrix": any("projection" in k or "camera_matrix" in k for k in keys),
                "has_object_state": any("object" in k.lower() or "transforms" in k.lower() or "rigid" in k.lower() for k in keys),
                "target_visible_ratio": None,
                "target_area_ratio_avg": None,
                "target_disappeared_consecutive_max": None,
            })
    except Exception as exc:
        info.update({"status": "error", "error": repr(exc)})
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated TDW/Physion-style HDF5 files.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--make_contact_sheet", action="store_true")
    args = parser.parse_args()
    hdf5_paths = sorted(args.root.rglob("*.hdf5")) + sorted(args.root.rglob("*.h5"))
    rows = [validate_hdf5(p) for p in hdf5_paths]
    ok = [r for r in rows if r.get("status") == "ok"]
    suitable = [r for r in ok if r.get("has_rgb") and r.get("has_depth") and r.get("has_id") and r.get("has_camera_pose")]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TDW Generation v2 Validation Report",
        "",
        f"Root: `{args.root}`",
        f"Generated HDF5 count: {len(rows)}",
        f"Validation ok count: {len(ok)}",
        f"Suitable for warmup count: {len(suitable)}",
        "",
        "| path | status | frames | rgb | depth | id | camera_pose | projection/camera_matrix | object_state |",
        "|---|---|---:|---|---|---|---|---|---|",
    ]
    for r in rows[:200]:
        lines.append(
            f"| `{r.get('path')}` | {r.get('status')} | {r.get('frame_count', '')} | {r.get('has_rgb', '')} | {r.get('has_depth', '')} | {r.get('has_id', '')} | {r.get('has_camera_pose', '')} | {r.get('has_projection_or_camera_matrix', '')} | {r.get('has_object_state', '')} |"
        )
    if not rows:
        lines += ["", "No generated HDF5 files were found. This is a blocker for actual validation, not a fake success."]
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_out = args.out.with_suffix(".json")
    json_out.write_text(json.dumps({"rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "hdf5_count": len(rows), "ok_count": len(ok), "suitable_for_warmup": len(suitable)}, indent=2))


if __name__ == "__main__":
    main()
