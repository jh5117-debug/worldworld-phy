from __future__ import annotations

import argparse
import json
from pathlib import Path


def _is_visible_motion_profile(profile: str | None) -> bool:
    return str(profile or "").startswith("warmup_visible_motion")


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter generated TDW v2 samples using validation JSON.")
    parser.add_argument("--validation_json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--profile", default=None)
    args = parser.parse_args()
    data = json.loads(args.validation_json.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    kept, rejected = [], []
    for row in rows:
        reasons = []
        if row.get("status") != "ok": reasons.append("hdf5_not_ok")
        for key in ["has_rgb", "has_depth", "has_id", "has_camera_pose"]:
            if not row.get(key): reasons.append(f"missing_{key}")
        if row.get("target_visible_ratio") is not None and row["target_visible_ratio"] < 0.75:
            reasons.append("low_target_visible_ratio")
        if _is_visible_motion_profile(args.profile):
            if row.get("too_static") is True:
                reasons.append("too_static")
            if row.get("too_extreme") is True:
                reasons.append("too_extreme")
            if row.get("delayed_camera_motion") is True:
                reasons.append("delayed_camera_motion")
            if row.get("duplicate_scene_hash") is True:
                reasons.append("duplicate_scene_hash")
            if row.get("suitable_for_visible_motion") is not True:
                reasons.append("not_suitable_for_visible_motion")
        target = kept if not reasons else rejected
        target.append({**row, "rejection_reasons": reasons})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = args.out.with_suffix(".md")
    report.write_text(
        "# TDW Generation v2 Filtering Report\n\n"
        f"Input: `{args.validation_json}`\n\n"
        f"Profile: `{args.profile or 'default'}`\n\n"
        f"Kept: {len(kept)}\n\nRejected: {len(rejected)}\n\n"
        "Rejected samples are not used for warmup. Reasons include missing HDF5 keys, low target visibility, incomplete camera metadata, too-static camera motion, or too-extreme foreground/camera behavior.\n",
        encoding="utf-8",
    )
    print(json.dumps({"kept": len(kept), "rejected": len(rejected), "out": str(args.out)}, indent=2))

if __name__ == "__main__":
    main()
