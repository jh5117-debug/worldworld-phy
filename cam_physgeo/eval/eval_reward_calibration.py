from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from cam_physgeo.rewards.corruption import make_corruption_records, make_contact_sheet
from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.utils.io import read_jsonl, write_jsonl


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--source", default="", choices=["", "physion_official", "physion_movingcam"])
    ap.add_argument("--out", default="reports/reward_calibration_physion")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--corruptions", nargs="+", default=["background_drift", "object_deformation", "global_freeze"])
    ap.add_argument("--save_debug", action="store_true")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--gpu_ids", default="")
    ap.add_argument("--strength", default="medium", choices=["low", "medium", "high"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    out_dir = Path(args.out)
    corr_dir = out_dir / "corruptions"
    rows = []
    drops: dict[str, list[float]] = defaultdict(list)
    wins: dict[str, int] = defaultdict(int)
    comps_by_type: dict[str, int] = defaultdict(int)
    clean_scores: list[float] = []
    corrupt_scores: list[float] = []
    clean_no_quality: list[float] = []
    corrupt_no_quality: list[float] = []
    clean_wins = 0
    comparisons = 0
    videos = []
    seen = 0
    for sample in read_jsonl(args.manifest):
        if args.source and sample.get("source") != args.source:
            continue
        if args.limit and seen >= args.limit:
            break
        records = make_corruption_records(
            sample,
            out_dir=corr_dir,
            dry_run=args.dry_run,
            types=args.corruptions,
            strength=args.strength,
            seed=seen,
        )
        clean_sample = dict(sample)
        if not clean_sample.get("video_path"):
            for record in records:
                if record.get("source_video"):
                    clean_sample["video_path"] = record["source_video"]
                    break
        clean = score_sample(clean_sample)
        clean["kind"] = "clean_gt"
        rows.append(clean)
        clean_scores.append(float(clean.get("reward_total") or 0.0))
        clean_no_quality.append(float(clean.get("reward_without_quality") or 0.0))
        for rec in records:
            corrupt_sample = dict(sample)
            corrupt_sample["candidate_video_path"] = rec["loser_video"]
            corrupt_sample["corruption_type"] = rec["corruption"]
            corrupt = score_sample(corrupt_sample)
            corrupt["kind"] = "corrupted_gt"
            corrupt["corruption"] = rec["corruption"]
            rows.append(corrupt)
            drop = float(clean.get("reward_total") or 0) - float(corrupt.get("reward_total") or 0)
            drops[rec["corruption"]].append(drop)
            corrupt_scores.append(float(corrupt.get("reward_total") or 0.0))
            corrupt_no_quality.append(float(corrupt.get("reward_without_quality") or 0.0))
            comparisons += 1
            comps_by_type[rec["corruption"]] += 1
            if drop > 0:
                clean_wins += 1
                wins[rec["corruption"]] += 1
            if rec.get("loser_video") and not str(rec["loser_video"]).startswith("corruption://"):
                videos.append(str(rec["loser_video"]))
        seen += 1
    summary = {
        "samples": seen,
        "rows": len(rows),
        "comparisons": comparisons,
        "device": args.device,
        "gpu_ids": args.gpu_ids,
        "strength": args.strength,
        "clean_average_reward_total": _mean(clean_scores),
        "corrupted_average_reward_total": _mean(corrupt_scores),
        "clean_average_reward_without_quality": _mean(clean_no_quality),
        "corrupted_average_reward_without_quality": _mean(corrupt_no_quality),
        "clean_gt_win_rate": clean_wins / comparisons if comparisons else None,
        "mean_drop_by_corruption": {k: sum(v) / len(v) for k, v in sorted(drops.items()) if v},
        "win_rate_by_corruption": {k: wins[k] / comps_by_type[k] for k in sorted(comps_by_type) if comps_by_type[k]},
        "dry_run": args.dry_run,
    }
    print(summary)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        write_jsonl(rows, out_dir / "scores.jsonl")
        with (out_dir / "per_corruption_table.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["corruption", "comparisons", "wins", "win_rate", "mean_drop"])
            writer.writeheader()
            for key in sorted(comps_by_type):
                vals = drops.get(key) or []
                writer.writerow(
                    {
                        "corruption": key,
                        "comparisons": comps_by_type[key],
                        "wins": wins[key],
                        "win_rate": wins[key] / comps_by_type[key] if comps_by_type[key] else "",
                        "mean_drop": sum(vals) / len(vals) if vals else "",
                    }
                )
        lines = [
            "# Physion Reward Calibration Smoke Report",
            "",
            f"- samples: {seen}",
            f"- comparisons: {comparisons}",
            f"- device requested: {args.device}",
            f"- gpu ids requested: {args.gpu_ids or 'none'}",
            f"- corruption strength: {args.strength}",
            f"- clean average R_total: {summary['clean_average_reward_total']}",
            f"- corrupted average R_total: {summary['corrupted_average_reward_total']}",
            f"- clean average without quality: {summary['clean_average_reward_without_quality']}",
            f"- corrupted average without quality: {summary['corrupted_average_reward_without_quality']}",
            f"- clean > corrupted win rate: {summary['clean_gt_win_rate']}",
            f"- reached 0.85 gate: {bool(summary['clean_gt_win_rate'] is not None and summary['clean_gt_win_rate'] >= 0.85)}",
            "",
            "## Mean Reward Drop",
        ]
        for key, value in summary["mean_drop_by_corruption"].items():
            lines.append(f"- {key}: {value:.4f}")
        lines.extend(["", "## Per-Corruption Win Rate"])
        for key, value in summary["win_rate_by_corruption"].items():
            lines.append(f"- {key}: {value:.3f}")
        lines.extend(
            [
                "",
                "## Notes",
                "- DINOv2/V-JEPA2/VideoMAE2 hooks are routed through the feature backend; when checkpoints are absent the smoke uses deterministic proxy visual features and records that fallback.",
                "- R_quality is kept low so blur/brightness does not dominate the physical-geometric reward.",
            ]
        )
        if summary["clean_gt_win_rate"] is not None and summary["clean_gt_win_rate"] < 0.85:
            lines.extend(["", "WARNING: reward has not reached the 0.85 clean-vs-corrupt gate; do not start DPO training yet."])
        (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if args.save_debug:
            make_contact_sheet(videos[:12], out_dir / "contact_sheets" / "corruptions.jpg")
    return 0


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


if __name__ == "__main__":
    raise SystemExit(main())
