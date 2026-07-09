from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from cam_physgeo.utils.io import read_jsonl


ALLOWED_PHYSICAL_GPUS = {"4", "5", "6", "7"}
FORBIDDEN_PHYSICAL_GPUS = {"0", "1", "2", "3"}


def visible_gpu_status() -> tuple[str, str]:
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    devices = [item.strip() for item in visible.split(",") if item.strip()]
    if not devices:
        return visible, "NO_VISIBLE_GPU_SET"
    forbidden = [item for item in devices if item in FORBIDDEN_PHYSICAL_GPUS or item not in ALLOWED_PHYSICAL_GPUS]
    if forbidden:
        return visible, "FORBIDDEN_GPU_VISIBLE:" + ",".join(forbidden)
    return visible, "GPU_POLICY_PASS"


def select_conditions(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    # Stable diversity-lite selection: round-robin by replay group, gravity label, then sample id.
    rows = sorted(rows, key=lambda r: (str(r.get("replay_group_id")), str(r.get("gravity_label")), str(r.get("sample_id"))))
    return rows[:n]


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for row in rows for k in row}) or ["status"]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_validation_decision(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return "MISSING"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return "UNREADABLE"
    return str(obj.get("decision") or obj.get("status") or "UNKNOWN")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--num_conditions", type=int, default=100)
    ap.add_argument("--models", default="original_fast")
    ap.add_argument("--gravity_modes", default="correct,wrong,default")
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--manifest_validation", default="reports/physeditworld_50h/conversion_validation/lingbot_val_manifest_validation.json")
    ap.add_argument("--dry_run", action="store_true")
    args = ap.parse_args(argv)
    rows = list(read_jsonl(args.manifest)) if Path(args.manifest).exists() else []
    validation_decision = read_validation_decision(args.manifest_validation)
    visible_gpus, gpu_policy = visible_gpu_status()
    selected = select_conditions(rows, args.num_conditions)
    report_rows: list[dict[str, Any]] = []
    if not selected:
        decision = "BASELINE_BLOCKED_EMPTY_MANIFEST"
    elif validation_decision != "LINGBOT_MANIFEST_SCHEMA_PASS":
        decision = "BASELINE_BLOCKED_MANIFEST_VALIDATION"
        selected = []
    elif gpu_policy.startswith("FORBIDDEN_GPU_VISIBLE"):
        decision = "BASELINE_BLOCKED_FORBIDDEN_GPU"
        selected = []
    elif args.dry_run:
        decision = "BASELINE_READY_DRY_RUN"
    elif gpu_policy == "NO_VISIBLE_GPU_SET":
        decision = "BASELINE_BLOCKED_NO_VISIBLE_GPU"
        selected = []
    else:
        decision = "BASELINE_BACKEND_NOT_CONNECTED"
    if selected:
        for row in selected:
            report_rows.append({
                "sample_id": row.get("sample_id"),
                "sample_dir": row.get("sample_dir"),
                "replay_group_id": row.get("replay_group_id"),
                "gravity_value": row.get("gravity_value"),
                "gravity_label": row.get("gravity_label"),
                "models": args.models,
                "gravity_modes": args.gravity_modes,
                "manifest_validation": args.manifest_validation,
                "validation_decision": validation_decision,
                "cuda_visible_devices": visible_gpus,
                "gpu_policy": gpu_policy,
                "status": "DRY_RUN_SELECTED" if args.dry_run else "BLOCKED_BACKEND_NOT_CONNECTED",
            })
    else:
        if not rows:
            reason = "input manifest has zero rows"
        elif decision == "BASELINE_BLOCKED_FORBIDDEN_GPU":
            reason = gpu_policy
        elif decision == "BASELINE_BLOCKED_NO_VISIBLE_GPU":
            reason = "CUDA_VISIBLE_DEVICES must be set to a subset of physical GPU4-7 for true rollout"
        else:
            reason = f"manifest validation decision is {validation_decision}"
        report_rows.append({"status": decision, "error_reason": reason, "manifest_validation": args.manifest_validation, "validation_decision": validation_decision, "cuda_visible_devices": visible_gpus, "gpu_policy": gpu_policy})
    write_csv(report_rows, args.report)
    source_counts = Counter(str(row.get("source") or "unknown") for row in selected)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(
        "# PhysEditWorld Baseline Rollout Summary\n\n"
        f"Decision: `{decision}`\n\n"
        f"- Input manifest: `{args.manifest}`\n"
        f"- Input rows: {len(rows)}\n"
        f"- Selected rows: {len(selected)}\n"
        f"- Manifest validation: `{args.manifest_validation}` decision=`{validation_decision}`\n"
        f"- Models requested: `{args.models}`\n"
        f"- Gravity modes requested: `{args.gravity_modes}`\n"
        f"- Output root: `{args.output_root}`\n"
        f"- CUDA_VISIBLE_DEVICES: `{visible_gpus}`\n"
        f"- GPU policy: `{gpu_policy}`\n"
        "- This wrapper does not perform image-only fallback or prefix_len=1 fallback.\n"
        "- True rollout remains blocked until valid PhysEditWorld LingBot manifest rows exist and a LingBot backend invocation is wired.\n\n"
        "## Source Counts\n\n"
        + "\n".join(f"- `{k}`: {v}" for k, v in sorted(source_counts.items()))
        + "\n"
    )
    print({"decision": decision, "input_rows": len(rows), "selected": len(selected), "report": args.report})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
