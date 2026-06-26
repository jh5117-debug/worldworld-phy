from __future__ import annotations

import argparse
from collections import Counter

from cam_physgeo.training.prefix_conditioning import build_prefix_plan
from cam_physgeo.utils.io import read_jsonl, write_json


def _validate_row(row: dict) -> str:
    try:
        prefix_len = int(row["prefix_len"])
        num_frames = len(row.get("target_frame_indices") or [])
        if num_frames <= 0:
            num_frames = int(row.get("num_frames") or 81)
        plan = build_prefix_plan(num_frames=num_frames, prefix_len=prefix_len, temporal_compression=int(row.get("temporal_compression") or 4))
        if int(row.get("prediction_start_frame")) != plan.prediction_start_frame:
            return "bad_prediction_start_frame"
        if list(row.get("loss_frame_indices") or []) != list(plan.loss_frame_indices):
            return "bad_loss_frame_indices"
        if list(row.get("reward_frame_indices") or []) != list(plan.reward_frame_indices):
            return "bad_reward_frame_indices"
        if not bool(row.get("eval_future_only", False)):
            return "eval_future_only_false"
    except Exception as exc:
        return f"exception:{type(exc).__name__}"
    return "ok"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate prefix-aware manifest masks and frame indices.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    rows = list(read_jsonl(args.manifest))
    statuses = [_validate_row(r) for r in rows]
    summary = {
        "manifest": args.manifest,
        "count": len(rows),
        "status_counts": dict(Counter(statuses)),
        "valid": all(s == "ok" for s in statuses),
    }
    write_json(summary, args.out)
    print(summary)
    return 0 if summary["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

