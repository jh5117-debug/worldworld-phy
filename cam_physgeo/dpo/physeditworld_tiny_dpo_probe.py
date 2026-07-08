from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

ALLOWED_PHYSICAL_GPUS = {"4", "5", "6", "7"}
FORBIDDEN_PHYSICAL_GPUS = {"0", "1", "2", "3"}
PAIR_READY_DECISIONS = {"READY_FOR_TINY_ANCHORED_DPO"}


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
        for token in ["READY_FOR_TINY_ANCHORED_DPO", "BLOCKED_INSUFFICIENT_DPO_PAIRS"]:
            if token in text:
                return token
    return "UNKNOWN"


def visible_gpu_status() -> tuple[str, str]:
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    devices = [d.strip() for d in visible.split(",") if d.strip()]
    if not devices:
        return visible, "NO_VISIBLE_GPU_SET"
    forbidden = [d for d in devices if d in FORBIDDEN_PHYSICAL_GPUS or d not in ALLOWED_PHYSICAL_GPUS]
    if forbidden:
        return visible, "FORBIDDEN_GPU_VISIBLE:" + ",".join(forbidden)
    return visible, "GPU_POLICY_PASS"


def write_csv(row: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = ["decision", "status", "error_reason", "pair_manifest", "pair_rows", "pair_gate_decision", "min_pairs", "steps", "cuda_visible_devices", "gpu_policy"]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in keys})


def write_decision(row: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(row: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PhysEditWorld Tiny Anchored DPO Gate Summary",
        "",
        f"Decision: `{row['decision']}`",
        "",
        f"- Status: `{row['status']}`",
        f"- Error reason: {row.get('error_reason') or 'none'}",
        f"- Pair manifest: `{row['pair_manifest']}` rows={row.get('pair_rows')}",
        f"- Pair gate decision: `{row.get('pair_gate_decision')}`",
        f"- Minimum pairs: `{row.get('min_pairs')}`",
        f"- Requested steps: `{row.get('steps')}`",
        f"- CUDA_VISIBLE_DEVICES: `{row.get('cuda_visible_devices')}`",
        f"- GPU policy: `{row.get('gpu_policy')}`",
        "",
        "No tiny DPO is allowed until at least 100 reviewed anchored pairs exist and the pair gate has passed.",
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="PhysEditWorld tiny anchored DPO safety gate")
    ap.add_argument("--pair_manifest", required=True)
    ap.add_argument("--pair_gate_summary", required=True)
    ap.add_argument("--min_pairs", type=int, default=100)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--dry_run", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pair_rows = count_jsonl(args.pair_manifest)
    pair_decision = read_decision(args.pair_gate_summary)
    visible, gpu_policy = visible_gpu_status()
    decision = "TINY_DPO_READY_DRY_RUN" if args.dry_run else "TINY_DPO_BACKEND_NOT_CONNECTED"
    status = "PASS" if args.dry_run else "BLOCKED"
    error = "" if args.dry_run else "real DPO backend is not connected in this gate scaffold"

    if gpu_policy.startswith("FORBIDDEN_GPU_VISIBLE"):
        decision, status, error = "TINY_DPO_BLOCKED_FORBIDDEN_GPU", "BLOCKED", gpu_policy
    elif pair_rows is None:
        decision, status, error = "TINY_DPO_BLOCKED_PAIR_MANIFEST_MISSING", "BLOCKED", "pair manifest missing"
    elif pair_rows < args.min_pairs:
        decision, status, error = "TINY_DPO_BLOCKED_INSUFFICIENT_PAIRS", "BLOCKED", f"pair rows {pair_rows} < {args.min_pairs}"
    elif pair_decision not in PAIR_READY_DECISIONS:
        decision, status, error = "TINY_DPO_BLOCKED_PAIR_GATE", "BLOCKED", "pair gate has not passed"

    row = {
        "decision": decision,
        "status": status,
        "error_reason": error,
        "pair_manifest": args.pair_manifest,
        "pair_rows": pair_rows,
        "pair_gate_decision": pair_decision,
        "min_pairs": args.min_pairs,
        "steps": args.steps,
        "cuda_visible_devices": visible,
        "gpu_policy": gpu_policy,
    }
    write_csv(row, args.report)
    write_decision(row, args.decision)
    write_summary(row, args.summary)
    print(json.dumps({"decision": decision, "status": status}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
