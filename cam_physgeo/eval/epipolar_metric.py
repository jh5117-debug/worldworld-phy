from __future__ import annotations

import argparse, csv, json
from pathlib import Path

import numpy as np

from cam_physgeo.rewards.epipolar import evaluate_epipolar_video


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest_csv", required=True)
    p.add_argument("--out_csv", required=True)
    p.add_argument("--vis_dir", default="")
    p.add_argument("--pose_convention", default="c2w", choices=["c2w", "w2c"])
    p.add_argument("--frame_i", type=int, default=0)
    p.add_argument("--frame_j", type=int, default=40)
    p.add_argument("--stride", type=int, default=24)
    args = p.parse_args()
    rows = list(csv.DictReader(open(args.manifest_csv, newline="", encoding="utf-8")))
    out_rows = []
    for row in rows:
        clip = Path(row.get("clip_dir") or Path(row["source_video"]).parent)
        video = Path(row.get("generated_video") or row.get("source_video"))
        poses = np.load(clip / "poses.npy")
        intr = np.load(clip / "intrinsics.npy")
        vis = Path(args.vis_dir) / f"{row.get('sample_id','sample')}_{row.get('model_label','model')}.jpg" if args.vis_dir else None
        result = evaluate_epipolar_video(video, poses, intr, frame_i=args.frame_i, frame_j=args.frame_j, pose_convention=args.pose_convention, stride=args.stride, visualization_path=vis)
        payload = {**row, **result.to_dict(), "visualization": str(vis) if vis else ""}
        out_rows.append(payload)
    keys = list(out_rows[0].keys()) if out_rows else []
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(out_rows)


if __name__ == "__main__":
    main()
