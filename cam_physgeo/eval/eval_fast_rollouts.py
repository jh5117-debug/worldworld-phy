from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from cam_physgeo.eval.make_contact_sheet import make_sheet, read_selected_video_frames
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


def scalar(row: dict[str, Any], key: str) -> float:
    return float(row.get(key, 0.0) or 0.0)


def write_pair_contact_sheet(sample_id: str, clean_video: Path, fast_video: Path, out_dir: Path) -> str | None:
    try:
        frames = []
        clean = read_selected_video_frames(clean_video, [0, 1, 2, 3, 4, 5, 6, 7, 8], thumb_size=(160, 96))
        fast = read_selected_video_frames(fast_video, [0, 1, 2, 3, 4, 5, 6, 7, 8], thumb_size=(160, 96))
        if clean:
            frames.extend(clean)
        if fast:
            frames.extend(fast)
        if not frames:
            return None
        out = out_dir / f"{sample_id}.jpg"
        make_sheet({"sample_id": sample_id, "template": "clean row then fast row", "camera_motion": "fast_rollout_reward_debug"}, frames, out)
        return str(out)
    except Exception:
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", required=True)
    ap.add_argument("--rollouts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--save_debug", action="store_true")
    ap.add_argument("--gpu_ids", default="")
    ap.add_argument("--debug_reward_breakdown", action="store_true")
    ap.add_argument("--confidence_weighted", action="store_true")
    ap.add_argument("--report_all_variants", action="store_true")
    args = ap.parse_args(argv)

    sample_root = Path(args.samples)
    rollout_root = Path(args.rollouts)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    pairs = []
    contact_dir = out / "contact_sheets"
    contact_dir.mkdir(exist_ok=True)
    for sample_dir in sample_dirs(sample_root, args.limit):
        target = sample_dir / "target.mp4"
        rollout = rollout_root / sample_dir.name / "generated.mp4"
        if not target.exists() or not rollout.exists():
            pairs.append({"sample_id": sample_dir.name, "status": "missing_rollout_or_target", "target_exists": target.exists(), "rollout_exists": rollout.exists()})
            continue
        clean = score_sample(make_sample(sample_dir, target, "clean_gt"))
        fast = score_sample(make_sample(sample_dir, rollout, "fast_zero_shot"))
        rows.extend([{**clean, "eval_label": "clean_gt"}, {**fast, "eval_label": "fast_zero_shot"}])
        clean_metric = clean["reward_total_confidence_weighted"] if args.confidence_weighted else clean["reward_total"]
        fast_metric = fast["reward_total_confidence_weighted"] if args.confidence_weighted else fast["reward_total"]
        sheet = write_pair_contact_sheet(sample_dir.name, target, rollout, contact_dir) if args.save_debug else None
        pairs.append({
            "sample_id": sample_dir.name,
            "status": "ok",
            "clean_reward": clean["reward_total"],
            "fast_reward": fast["reward_total"],
            "clean_gt_wins": clean["reward_total"] > fast["reward_total"],
            "clean_reward_confidence_weighted": clean.get("reward_total_confidence_weighted"),
            "fast_reward_confidence_weighted": fast.get("reward_total_confidence_weighted"),
            "clean_gt_wins_confidence_weighted": clean_metric > fast_metric,
            "clean_reward_no_quality": clean.get("reward_without_quality"),
            "fast_reward_no_quality": fast.get("reward_without_quality"),
            "clean_geometry_only": clean.get("R_geometry_only"),
            "fast_geometry_only": fast.get("R_geometry_only"),
            "clean_identity_only": clean.get("R_identity_only"),
            "fast_identity_only": fast.get("R_identity_only"),
            "clean_motion_only": clean.get("R_motion_only"),
            "fast_motion_only": fast.get("R_motion_only"),
            "clean_quality_only": clean.get("R_quality_only"),
            "fast_quality_only": fast.get("R_quality_only"),
            "clean_freeze_penalty": clean.get("P_freeze"),
            "fast_freeze_penalty": fast.get("P_freeze"),
            "clean_reward_confidence_overall": clean.get("reward_confidence_overall"),
            "fast_reward_confidence_overall": fast.get("reward_confidence_overall"),
            "clean_provisional": clean.get("reward_provisional"),
            "fast_provisional": fast.get("reward_provisional"),
            "contact_sheet": sheet,
            "component_delta_clean_minus_fast": {
                key: component_score(clean, key) - component_score(fast, key)
                for key in ["bg", "cam", "fg", "phys", "reobs", "quality", "freeze"]
            },
            "variant_delta_clean_minus_fast": {
                "R_total": scalar(clean, "R_total") - scalar(fast, "R_total"),
                "R_total_confidence_weighted": scalar(clean, "R_total_confidence_weighted") - scalar(fast, "R_total_confidence_weighted"),
                "R_total_no_quality": scalar(clean, "R_total_no_quality") - scalar(fast, "R_total_no_quality"),
                "R_geometry_only": scalar(clean, "R_geometry_only") - scalar(fast, "R_geometry_only"),
                "R_identity_only": scalar(clean, "R_identity_only") - scalar(fast, "R_identity_only"),
                "R_motion_only": scalar(clean, "R_motion_only") - scalar(fast, "R_motion_only"),
                "R_quality_only": scalar(clean, "R_quality_only") - scalar(fast, "R_quality_only"),
                "P_freeze": scalar(clean, "P_freeze") - scalar(fast, "P_freeze"),
            },
        })
    write_jsonl(rows, out / "scores.jsonl")
    ok_pairs = [p for p in pairs if p.get("status") == "ok"]
    count = len(ok_pairs)
    clean_avg = sum(p["clean_reward"] for p in ok_pairs) / count if count else None
    fast_avg = sum(p["fast_reward"] for p in ok_pairs) / count if count else None
    win_rate = sum(1 for p in ok_pairs if p["clean_gt_wins"]) / count if count else None
    clean_conf_avg = sum(float(p["clean_reward_confidence_weighted"] or 0.0) for p in ok_pairs) / count if count else None
    fast_conf_avg = sum(float(p["fast_reward_confidence_weighted"] or 0.0) for p in ok_pairs) / count if count else None
    win_rate_conf = sum(1 for p in ok_pairs if p["clean_gt_wins_confidence_weighted"]) / count if count else None
    with (out / "per_metric_table.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "sample_id",
            "clean_reward",
            "fast_reward",
            "clean_gt_wins",
            "clean_confidence_weighted",
            "fast_confidence_weighted",
            "clean_gt_wins_confidence_weighted",
            "clean_no_quality",
            "fast_no_quality",
            "clean_geometry_only",
            "fast_geometry_only",
            "clean_identity_only",
            "fast_identity_only",
            "clean_motion_only",
            "fast_motion_only",
            "clean_quality_only",
            "fast_quality_only",
            "clean_freeze",
            "fast_freeze",
            "clean_confidence",
            "fast_confidence",
            "delta_bg",
            "delta_cam",
            "delta_fg",
            "delta_phys",
            "delta_reobs",
            "delta_quality",
            "delta_freeze",
        ])
        for p in ok_pairs:
            d = p["component_delta_clean_minus_fast"]
            writer.writerow([
                p["sample_id"],
                p["clean_reward"],
                p["fast_reward"],
                p["clean_gt_wins"],
                p["clean_reward_confidence_weighted"],
                p["fast_reward_confidence_weighted"],
                p["clean_gt_wins_confidence_weighted"],
                p["clean_reward_no_quality"],
                p["fast_reward_no_quality"],
                p["clean_geometry_only"],
                p["fast_geometry_only"],
                p["clean_identity_only"],
                p["fast_identity_only"],
                p["clean_motion_only"],
                p["fast_motion_only"],
                p["clean_quality_only"],
                p["fast_quality_only"],
                p["clean_freeze_penalty"],
                p["fast_freeze_penalty"],
                p["clean_reward_confidence_overall"],
                p["fast_reward_confidence_overall"],
                d["bg"],
                d["cam"],
                d["fg"],
                d["phys"],
                d["reobs"],
                d["quality"],
                d["freeze"],
            ])
    summary = [
        "# Fast Zero-Shot Rollout Reward Report",
        "",
        f"- Samples considered: {len(pairs)}",
        f"- Valid clean/Fast pairs: {count}",
        f"- Clean GT avg reward: {clean_avg}",
        f"- Fast rollout avg reward: {fast_avg}",
        f"- Clean > Fast win rate: {win_rate}",
        f"- Clean GT avg confidence-weighted reward: {clean_conf_avg}",
        f"- Fast rollout avg confidence-weighted reward: {fast_conf_avg}",
        f"- Clean > Fast confidence-weighted win rate: {win_rate_conf}",
        "- Reward confidence is now reported per component. Fallback/missing backends do not contribute high confidence.",
        "- DINO/V-JEPA actual forward: not used in this reward path unless backend report says otherwise; proxy visual signatures are active.",
        "- Optical flow actual forward: not used yet; frame-diff proxy is active.",
        "- This report is not a DPO-ready preference source unless camera condition and reward backends are both reliable.",
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
