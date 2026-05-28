from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.utils.io import write_jsonl


def sample_dirs(root: Path, limit: int) -> list[Path]:
    dirs = [p for p in sorted(root.iterdir()) if p.is_dir()] if root.exists() else []
    return dirs[:limit] if limit else dirs


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def make_sample(sample_dir: Path, video: Path, label: str) -> dict[str, Any]:
    meta = read_json(sample_dir / "metadata.json")
    return {
        "sample_id": sample_dir.name,
        "source": "physion_movingcam",
        "template": meta.get("template", "unknown"),
        "camera_motion": meta.get("camera_motion", "unknown"),
        "video_path": str(video),
        "candidate_video_path": str(video),
        "poses_path": str(sample_dir / "poses.npy"),
        "intrinsics_path": str(sample_dir / "intrinsics.npy"),
        "id_path": str(sample_dir / "id_mask.npy") if (sample_dir / "id_mask.npy").exists() else None,
        "depth_path": str(sample_dir / "depth.npy") if (sample_dir / "depth.npy").exists() else None,
        "has_id_mask": (sample_dir / "id_mask.npy").exists(),
        "has_depth": (sample_dir / "depth.npy").exists(),
        "has_camera_pose": (sample_dir / "poses.npy").exists(),
        "has_intrinsics": (sample_dir / "intrinsics.npy").exists(),
        "has_reobserve": "reobserve" in str(meta.get("camera_motion", "")),
        "eval_label": label,
    }


def component_score(row: dict[str, Any], name: str) -> float:
    comp = row.get("components", {}).get(name, {})
    if name == "freeze":
        return float(comp.get("penalty", 0.0) or 0.0)
    return float(comp.get("score", 0.0) or 0.0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", required=True)
    ap.add_argument("--rollouts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--save_debug", action="store_true")
    ap.add_argument("--gpu_ids", default="")
    args = ap.parse_args(argv)

    sample_root = Path(args.samples)
    rollout_root = Path(args.rollouts)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    pairs = []
    for sample_dir in sample_dirs(sample_root, args.limit):
        target = sample_dir / "target.mp4"
        rollout = rollout_root / sample_dir.name / "generated.mp4"
        if not target.exists() or not rollout.exists():
            pairs.append({"sample_id": sample_dir.name, "status": "missing_rollout_or_target", "target_exists": target.exists(), "rollout_exists": rollout.exists()})
            continue
        clean = score_sample(make_sample(sample_dir, target, "clean_gt"))
        fast = score_sample(make_sample(sample_dir, rollout, "fast_zero_shot"))
        rows.extend([{**clean, "eval_label": "clean_gt"}, {**fast, "eval_label": "fast_zero_shot"}])
        pairs.append({
            "sample_id": sample_dir.name,
            "status": "ok",
            "clean_reward": clean["reward_total"],
            "fast_reward": fast["reward_total"],
            "clean_gt_wins": clean["reward_total"] > fast["reward_total"],
            "component_delta_clean_minus_fast": {
                key: component_score(clean, key) - component_score(fast, key)
                for key in ["bg", "cam", "fg", "phys", "reobs", "quality", "freeze"]
            },
        })
    write_jsonl(rows, out / "scores.jsonl")
    ok_pairs = [p for p in pairs if p.get("status") == "ok"]
    count = len(ok_pairs)
    clean_avg = sum(p["clean_reward"] for p in ok_pairs) / count if count else None
    fast_avg = sum(p["fast_reward"] for p in ok_pairs) / count if count else None
    win_rate = sum(1 for p in ok_pairs if p["clean_gt_wins"]) / count if count else None
    with (out / "per_metric_table.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "clean_reward", "fast_reward", "clean_gt_wins", "delta_bg", "delta_cam", "delta_fg", "delta_phys", "delta_reobs", "delta_quality", "delta_freeze"])
        for p in ok_pairs:
            d = p["component_delta_clean_minus_fast"]
            writer.writerow([p["sample_id"], p["clean_reward"], p["fast_reward"], p["clean_gt_wins"], d["bg"], d["cam"], d["fg"], d["phys"], d["reobs"], d["quality"], d["freeze"]])
    summary = [
        "# Fast Zero-Shot Rollout Reward Report",
        "",
        f"- Samples considered: {len(pairs)}",
        f"- Valid clean/Fast pairs: {count}",
        f"- Clean GT avg reward: {clean_avg}",
        f"- Fast rollout avg reward: {fast_avg}",
        f"- Clean > Fast win rate: {win_rate}",
        "- DINO/V-JEPA actual forward: not used in this reward path unless backend report says otherwise; proxy visual signatures are active.",
        "- Optical flow actual forward: not used yet; frame-diff proxy is active.",
        "",
        "## Pair Status",
    ]
    for p in pairs:
        summary.append(f"- `{p['sample_id']}`: {p}")
    (out / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    (out / "contact_sheets").mkdir(exist_ok=True)
    print({"pairs": len(pairs), "valid_pairs": count, "clean_avg": clean_avg, "fast_avg": fast_avg, "win_rate": win_rate, "out": str(out)})
    return 0 if count else 2


if __name__ == "__main__":
    raise SystemExit(main())
