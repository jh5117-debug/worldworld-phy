from __future__ import annotations

import argparse
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from cam_physgeo.rewards.corruption import CORRUPTIONS, make_corruption_records
from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.utils.io import load_yaml, read_jsonl, write_jsonl


def parse_corruptions(values: list[str] | str) -> list[str]:
    if isinstance(values, str):
        raw = values.replace(",", " ").split()
    else:
        raw = []
        for value in values:
            raw.extend(str(value).replace(",", " ").split())
    return [c for c in raw if c in CORRUPTIONS]


def make_gt_vs_corrupt_pairs(
    sample: dict,
    *,
    corruptions: list[str],
    save_videos: str,
    weights: dict | None = None,
    min_margin: float = 0.0,
    dry_run: bool = False,
) -> tuple[list[dict], list[dict]]:
    pairs: list[dict] = []
    rejected: list[dict] = []
    if not sample.get("has_camera_pose") or not sample.get("has_intrinsics"):
        return [], [{"sample_id": sample.get("sample_id"), "reason": "missing_camera_condition"}]
    if not sample.get("video_path") and not sample.get("hdf5_path"):
        return [], [{"sample_id": sample.get("sample_id"), "reason": "missing_video_or_hdf5_rgb"}]
    records = make_corruption_records(sample, out_dir=save_videos, dry_run=dry_run, types=corruptions)
    clean_sample = dict(sample)
    if not clean_sample.get("video_path"):
        for record in records:
            if record.get("source_video"):
                clean_sample["video_path"] = record["source_video"]
                break
    clean_reward = score_sample(clean_sample, weights=weights)
    for record in records:
        corruption = record["corruption"]
        loser_video = record["loser_video"]
        if str(loser_video).startswith("corruption://") or (not dry_run and not Path(str(loser_video)).exists()):
            rejected.append({"sample_id": sample.get("sample_id"), "corruption": corruption, "reason": "corruption_video_missing"})
            continue
        loser_sample = dict(sample)
        loser_sample["candidate_video_path"] = loser_video
        loser_sample["corruption_type"] = corruption
        loser_reward = score_sample(loser_sample, weights=weights)
        margin = float(clean_reward.get("reward_total") or 0.0) - float(loser_reward.get("reward_total") or 0.0)
        if margin < min_margin:
            rejected.append(
                {
                    "sample_id": sample.get("sample_id"),
                    "corruption": corruption,
                    "reason": "margin_below_threshold",
                    "margin": margin,
                }
            )
            continue
        sid = str(sample.get("sample_id"))
        pair_id = "pair_" + hashlib.sha1(f"{sid}:{corruption}:{loser_video}".encode()).hexdigest()[:12]
        pairs.append(
            {
                "pair_id": pair_id,
                "condition": {
                    "image": sample.get("image_path"),
                    "prefix": sample.get("prefix_path"),
                    "prompt": sample.get("prompt_path"),
                    "poses": sample.get("poses_path"),
                    "intrinsics": sample.get("intrinsics_path"),
                    "use_action": False,
                },
                "winner": {"video": clean_sample.get("video_path"), "source": "clean_physion_gt", "reward": clean_reward},
                "loser": {"video": loser_video, "source": "corrupted_gt", "reward": loser_reward},
                "pair_type": "gt_vs_corrupt",
                "corruption": corruption,
                "margin": margin,
                "weight": 1.0,
                "quality_flags": list(sample.get("quality_flags") or []) + list(record.get("quality_flags") or []),
            }
        )
    return pairs, rejected


def write_report(path: str | Path, pairs: list[dict], rejected: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    by_corr = Counter(row.get("corruption") for row in pairs)
    rej = Counter(row.get("reason") for row in rejected)
    margins = [float(row.get("margin") or 0.0) for row in pairs]
    lines = [
        "# Physion DPO Pair Builder Report",
        "",
        f"- total pairs: {len(pairs)}",
        f"- rejected pairs: {len(rejected)}",
        f"- mean margin: {sum(margins) / len(margins):.4f}" if margins else "- mean margin: n/a",
        "",
        "## Kept By Corruption",
    ]
    for key, value in sorted(by_corr.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Rejected"])
    for key, value in sorted(rej.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Sample Pairs"])
    for row in pairs[:5]:
        lines.append(f"- {row['pair_id']}: {row['winner']['video']} > {row['loser']['video']} margin={row['margin']:.4f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--source", default="", choices=["", "physion_official", "physion_movingcam"])
    ap.add_argument("--pair_types", nargs="+", default=["gt_vs_corrupt"])
    ap.add_argument("--config", default="")
    ap.add_argument("--out", default="manifests/dpo_pairs_physion_gt_vs_corrupt.jsonl")
    ap.add_argument("--corruptions", nargs="+", default=["background_drift", "global_freeze"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--min_margin", type=float, default=0.05)
    ap.add_argument("--save_videos", default="outputs/dpo_pair_physion")
    ap.add_argument("--save_report", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if "gt_vs_corrupt" not in args.pair_types:
        raise SystemExit("Only gt_vs_corrupt is implemented before LingBot rollout generation.")
    cfg = load_yaml(args.config) if args.config else {}
    weights = (cfg.get("reward_weights") or cfg.get("weights") or {}) if isinstance(cfg, dict) else {}
    corruptions = parse_corruptions(args.corruptions)
    pairs: list[dict] = []
    rejected: list[dict] = []
    seen = 0
    for sample in read_jsonl(args.manifest):
        if args.source and sample.get("source") != args.source:
            continue
        if args.limit and seen >= args.limit:
            break
        new_pairs, new_rejected = make_gt_vs_corrupt_pairs(
            sample,
            corruptions=corruptions,
            save_videos=args.save_videos,
            weights=weights,
            min_margin=args.min_margin,
            dry_run=args.dry_run,
        )
        pairs.extend(new_pairs)
        rejected.extend(new_rejected)
        seen += 1
    print({"samples": seen, "pairs": len(pairs), "rejected": len(rejected), "out": args.out, "dry_run": args.dry_run})
    if not args.dry_run:
        write_jsonl(pairs, args.out)
        if args.save_report:
            write_report(args.save_report, pairs, rejected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
