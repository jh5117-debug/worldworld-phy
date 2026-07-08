from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from cam_physgeo.utils.io import read_jsonl


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
    selected = select_conditions(rows, args.num_conditions)
    report_rows: list[dict[str, Any]] = []
    if not selected:
        decision = "BASELINE_BLOCKED_EMPTY_MANIFEST"
    elif validation_decision != "LINGBOT_MANIFEST_SCHEMA_PASS":
        decision = "BASELINE_BLOCKED_MANIFEST_VALIDATION"
        selected = []
    elif args.dry_run:
        decision = "BASELINE_READY_DRY_RUN"
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
                "status": "DRY_RUN_SELECTED" if args.dry_run else "BLOCKED_BACKEND_NOT_CONNECTED",
            })
    else:
        reason = "input manifest has zero rows" if not rows else f"manifest validation decision is {validation_decision}"
        report_rows.append({"status": decision, "error_reason": reason, "manifest_validation": args.manifest_validation, "validation_decision": validation_decision})
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
