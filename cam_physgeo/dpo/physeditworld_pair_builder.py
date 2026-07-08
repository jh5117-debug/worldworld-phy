from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

PASS_DECISIONS = {"WARMUP_GATE_PASS"}


def count_jsonl(path: str | Path) -> int | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def read_decision(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return "MISSING"
    text = p.read_text(encoding="utf-8", errors="ignore")
    try:
        obj = json.loads(text)
        return str(obj.get("decision") or obj.get("status") or "UNKNOWN")
    except Exception:
        for token in ["WARMUP_GATE_PASS", "WARMUP_VIDEO_METRIC_FAIL", "WARMUP_GRAVITY_SIGNAL_FAIL", "WARMUP_RUNTIME_BLOCKED"]:
            if token in text:
                return token
    return "UNKNOWN"


def write_empty_jsonl(path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("", encoding="utf-8")


def write_audit(row: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = ["decision", "status", "error_reason", "warmup_decision", "gt_rows", "rollout_rows", "ready_pairs", "min_pairs"]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in keys})


def write_summary(row: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PhysEditWorld Anchored Pair Builder Summary",
        "",
        f"Decision: `{row['decision']}`",
        "",
        f"- Status: `{row['status']}`",
        f"- Error reason: {row.get('error_reason') or 'none'}",
        f"- Warm-up decision: `{row.get('warmup_decision')}`",
        f"- GT rows: `{row.get('gt_rows')}`",
        f"- Rollout rows: `{row.get('rollout_rows')}`",
        f"- Ready pairs: `{row.get('ready_pairs')}`",
        f"- Minimum pairs: `{row.get('min_pairs')}`",
        "",
        "No pair is admitted unless warm-up checkpoint video/metric gate has passed and every loser has visual-audit evidence.",
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="PhysEditWorld anchored DPO pair gate/builder")
    ap.add_argument("--warmup_decision", required=True)
    ap.add_argument("--gt_manifest", required=True)
    ap.add_argument("--rollout_manifest", default="")
    ap.add_argument("--output", required=True)
    ap.add_argument("--audit", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--min_pairs", type=int, default=100)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    warmup_decision = read_decision(args.warmup_decision)
    gt_rows = count_jsonl(args.gt_manifest)
    rollout_rows = count_jsonl(args.rollout_manifest) if args.rollout_manifest else None
    decision = "READY_FOR_TINY_ANCHORED_DPO"
    status = "PASS"
    error = ""
    ready_pairs = 0

    if warmup_decision not in PASS_DECISIONS:
        decision, status, error = "PAIR_BUILDER_BLOCKED_WARMUP_GATE", "BLOCKED", "warm-up gate has not passed"
    elif gt_rows is None:
        decision, status, error = "PAIR_BUILDER_BLOCKED_GT_MANIFEST_MISSING", "BLOCKED", "GT manifest missing"
    elif gt_rows == 0:
        decision, status, error = "PAIR_BUILDER_BLOCKED_EMPTY_GT_MANIFEST", "BLOCKED", "GT manifest has zero rows"
    elif rollout_rows is None:
        decision, status, error = "PAIR_BUILDER_BLOCKED_ROLLOUT_MANIFEST_MISSING", "BLOCKED", "rollout manifest missing"
    elif rollout_rows == 0:
        decision, status, error = "PAIR_BUILDER_BLOCKED_EMPTY_ROLLOUT_MANIFEST", "BLOCKED", "rollout manifest has zero rows"
    else:
        decision, status, error = "PAIR_BUILDER_BACKEND_NOT_CONNECTED", "BLOCKED", "pair construction backend awaits real checkpoint rollout and visual audit inputs"

    write_empty_jsonl(args.output)
    row = {
        "decision": decision,
        "status": status,
        "error_reason": error,
        "warmup_decision": warmup_decision,
        "gt_rows": gt_rows,
        "rollout_rows": rollout_rows,
        "ready_pairs": ready_pairs,
        "min_pairs": args.min_pairs,
    }
    write_audit(row, args.audit)
    write_summary(row, args.summary)
    print(json.dumps({"decision": decision, "status": status, "output": args.output}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
