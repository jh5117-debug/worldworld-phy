from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

ALLOWED_PHYSICAL_GPUS = {"4", "5", "6", "7"}
FORBIDDEN_PHYSICAL_GPUS = {"0", "1", "2", "3"}


def count_jsonl(path: str | Path) -> int | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def visible_gpu_status() -> tuple[str, str]:
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    devices = [d.strip() for d in visible.split(",") if d.strip()]
    if not devices:
        return visible, "NO_VISIBLE_GPU_SET"
    forbidden = [d for d in devices if d in FORBIDDEN_PHYSICAL_GPUS or d not in ALLOWED_PHYSICAL_GPUS]
    if forbidden:
        return visible, "FORBIDDEN_GPU_VISIBLE:" + ",".join(forbidden)
    return visible, "GPU_POLICY_PASS"


def parse_steps(text: str) -> list[str]:
    out = []
    for part in text.split(","):
        item = part.strip()
        if item:
            out.append(item)
    return out


def write_csv(rows: list[dict[str, Any]], path: str | Path, keys: list[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in keys})


def write_summary(row: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PhysEditWorld Checkpoint Eval Gate Summary",
        "",
        f"Decision: `{row['decision']}`",
        "",
        f"- Status: `{row['status']}`",
        f"- Error reason: {row.get('error_reason') or 'none'}",
        f"- Eval manifest: `{row['eval_manifest']}` rows={row.get('eval_rows')}",
        f"- Checkpoint root: `{row['checkpoint_root']}`",
        f"- Steps: `{row.get('steps')}`",
        f"- CUDA_VISIBLE_DEVICES: `{row.get('cuda_visible_devices')}`",
        f"- GPU policy: `{row.get('gpu_policy')}`",
        "",
        "This gate does not perform image-only or prefix_len=1 fallback. True rollout, metrics, and Codex visual audit are required before any warm-up checkpoint can pass.",
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decision(row: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="PhysEditWorld checkpoint rollout/metric/audit gate")
    ap.add_argument("--eval_manifest", required=True)
    ap.add_argument("--checkpoint_root", required=True)
    ap.add_argument("--steps", default="0,500,1000,2000")
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--gravity_metrics", required=True)
    ap.add_argument("--video_audit", required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--dry_run", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    eval_rows = count_jsonl(args.eval_manifest)
    visible, gpu_policy = visible_gpu_status()
    steps = parse_steps(args.steps)
    decision = "CHECKPOINT_EVAL_READY_DRY_RUN" if args.dry_run else "CHECKPOINT_EVAL_BACKEND_NOT_CONNECTED"
    status = "PASS" if args.dry_run else "BLOCKED"
    error = "" if args.dry_run else "real V2V-5 rollout backend is not connected in this gate scaffold"

    if gpu_policy.startswith("FORBIDDEN_GPU_VISIBLE"):
        decision, status, error = "CHECKPOINT_EVAL_BLOCKED_FORBIDDEN_GPU", "BLOCKED", gpu_policy
    elif eval_rows is None:
        decision, status, error = "CHECKPOINT_EVAL_BLOCKED_EVAL_MANIFEST_MISSING", "BLOCKED", "eval manifest missing"
    elif eval_rows == 0:
        decision, status, error = "CHECKPOINT_EVAL_BLOCKED_EMPTY_EVAL_MANIFEST", "BLOCKED", "eval manifest has zero rows"
    elif not Path(args.checkpoint_root).exists():
        decision, status, error = "CHECKPOINT_EVAL_BLOCKED_CHECKPOINT_ROOT_MISSING", "BLOCKED", "checkpoint root missing"

    row = {
        "decision": decision,
        "status": status,
        "error_reason": error,
        "eval_manifest": args.eval_manifest,
        "eval_rows": eval_rows,
        "checkpoint_root": args.checkpoint_root,
        "steps": ",".join(steps),
        "cuda_visible_devices": visible,
        "gpu_policy": gpu_policy,
        "output_root": args.output_root,
    }
    write_csv([row], args.report, ["decision", "status", "error_reason", "eval_manifest", "eval_rows", "checkpoint_root", "steps", "cuda_visible_devices", "gpu_policy", "output_root"])
    write_csv([], args.gravity_metrics, ["checkpoint", "sample_id", "gravity_ordering", "airtime_error", "fall_speed_error", "contact_timing_error", "status"])
    write_csv([], args.video_audit, ["sample_id", "checkpoint", "gravity_response", "action_following", "camera_following", "freeze", "visual_quality", "written_reason", "reviewed", "status"])
    write_decision(row, args.decision)
    write_summary(row, args.summary)
    print(json.dumps({"decision": decision, "status": status}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
