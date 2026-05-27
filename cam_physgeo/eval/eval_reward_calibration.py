from __future__ import annotations

import argparse
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
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    out_dir = Path(args.out)
    corr_dir = out_dir / "corruptions"
    rows = []
    drops: dict[str, list[float]] = defaultdict(list)
    clean_wins = 0
    comparisons = 0
    videos = []
    seen = 0
    for sample in read_jsonl(args.manifest):
        if args.source and sample.get("source") != args.source:
            continue
        if args.limit and seen >= args.limit:
            break
        clean = score_sample(sample)
        clean["kind"] = "clean_gt"
        rows.append(clean)
        records = make_corruption_records(sample, out_dir=corr_dir, dry_run=args.dry_run, types=args.corruptions)
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
            comparisons += 1
            if drop > 0:
                clean_wins += 1
            if rec.get("loser_video") and not str(rec["loser_video"]).startswith("corruption://"):
                videos.append(str(rec["loser_video"]))
        seen += 1
    summary = {
        "samples": seen,
        "rows": len(rows),
        "comparisons": comparisons,
        "clean_gt_win_rate": clean_wins / comparisons if comparisons else None,
        "mean_drop_by_corruption": {k: sum(v) / len(v) for k, v in sorted(drops.items()) if v},
        "dry_run": args.dry_run,
    }
    print(summary)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        write_jsonl(rows, out_dir / "scores.jsonl")
        lines = [
            "# Physion Reward Calibration Smoke Report",
            "",
            f"- samples: {seen}",
            f"- comparisons: {comparisons}",
            f"- clean > corrupted win rate: {summary['clean_gt_win_rate']}",
            "",
            "## Mean Reward Drop",
        ]
        for key, value in summary["mean_drop_by_corruption"].items():
            lines.append(f"- {key}: {value:.4f}")
        if summary["clean_gt_win_rate"] is not None and summary["clean_gt_win_rate"] < 0.7:
            lines.extend(["", "WARNING: reward does not yet separate clean and corrupted GT reliably."])
        (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if args.save_debug:
            make_contact_sheet(videos[:12], out_dir / "contact_sheets" / "corruptions.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
