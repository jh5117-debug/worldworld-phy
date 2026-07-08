from __future__ import annotations

import argparse
import csv
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BLOCKED_PREFIXES = ("BLOCKED",)
READY_MANIFEST_INIT = {"PHYS_EDITWORLD_EMPTY_MANIFESTS_INITIALIZED", "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT"}
READY_ROOT_SCHEMA_PROBE = "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"
READY_READINESS = "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT"
READY_ASSET_VALIDATION = "MIGRATION_ASSET_VALIDATION_PASS"
READY_APPROVED_COPY = {"APPROVED_COPY_DRYRUN_READY", "APPROVED_COPY_EXECUTED"}


@dataclass
class PhaseStatus:
    phase: str
    decision: str
    status: str
    source: str
    next_action: str = ""
    error_reason: str = ""


def read_json_decision(path: str | Path) -> tuple[str, str, str]:
    p = Path(path)
    if not p.exists():
        return "MISSING", "BLOCKED", "file missing"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        decision = str(obj.get("decision") or obj.get("status") or "UNKNOWN")
        status = str(obj.get("status") or ("BLOCKED" if "BLOCKED" in decision or "MISSING" in decision else "UNKNOWN"))
        error = str(obj.get("error_reason") or "")
        return decision, status, error
    except Exception as exc:
        return "UNREADABLE", "BLOCKED", repr(exc)


def read_md_decision(path: str | Path) -> tuple[str, str, str]:
    p = Path(path)
    if not p.exists():
        return "MISSING", "BLOCKED", "file missing"
    text = p.read_text(encoding="utf-8", errors="ignore")
    decision = "UNKNOWN"
    for line in text.splitlines():
        if line.strip().startswith("Decision:"):
            decision = line.split("`", 2)[1] if "`" in line else line.split(":", 1)[-1].strip()
            break
    status = "BLOCKED" if "BLOCKED" in decision or "FAIL" in decision or decision == "MISSING" else "PASS"
    return decision, status, ""


def status_for_expected_decision(decision: str, pass_values: set[str]) -> str:
    if decision in pass_values:
        return "PASS"
    if decision == "MISSING" or decision.startswith("UNREADABLE"):
        return "BLOCKED"
    if any(marker in decision for marker in ("BLOCKED", "FAIL", "WAITING", "MISSING", "NEEDS", "REJECT", "NONE_STRONG")):
        return "BLOCKED"
    return "BLOCKED"


def decision_gate_row(phase: str, path: str, pass_values: set[str], blocked_next_action: str, pass_next_action: str = "") -> PhaseStatus:
    decision, _status, error = read_json_decision(path)
    status = status_for_expected_decision(decision, pass_values)
    return PhaseStatus(
        phase,
        decision,
        status,
        path,
        next_action=pass_next_action if status == "PASS" else blocked_next_action,
        error_reason=error,
    )


def run_command(cmd: list[str], dry_run: bool) -> tuple[int, str]:
    if dry_run:
        return 0, "DRY_RUN_SKIPPED"
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return proc.returncode, proc.stdout[-4000:]


def write_csv(rows: list[PhaseStatus], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = ["phase", "decision", "status", "source", "next_action", "error_reason"]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: asdict(row).get(k, "") for k in keys})


def write_json(rows: list[PhaseStatus], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "phases": [asdict(row) for row in rows],
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[PhaseStatus], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# PhysEditWorld Pipeline Gate Summary", "", f"Decision: `{decision}`", "", "## Phases", ""]
    for row in rows:
        lines.append(f"- `{row.phase}`: `{row.decision}` from `{row.source}`")
        if row.error_reason:
            lines.append(f"  - blocker: {row.error_reason}")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    lines.extend([
        "",
        "## Safety",
        "",
        "This orchestrator is a gate collector. It does not launch large DPO, train400, StageB, GRPO, broad-LoRA, checkpoint deletion, or any local_assets push.",
        "When prerequisites are blocked it stops before rollout, warm-up, pair construction, and tiny DPO.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def pipeline_decision(rows: list[PhaseStatus]) -> str:
    if not rows:
        return "PIPELINE_GATE_NO_ROWS"
    first_block = next((row for row in rows if row.status == "BLOCKED" or "BLOCKED" in row.decision or row.decision == "MISSING"), None)
    if first_block:
        return "PIPELINE_BLOCKED_AT_" + first_block.phase.upper()
    return "PIPELINE_READY_FOR_NEXT_EXECUTION_STEP"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="PhysEditWorld 50h safe phase gate orchestrator")
    ap.add_argument("--run_readiness", action="store_true")
    ap.add_argument("--dry_run", action="store_true")
    ap.add_argument("--output_csv", default="reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.csv")
    ap.add_argument("--output_json", default="reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json")
    ap.add_argument("--summary", default="reports/physeditworld_50h/pipeline_gate/pipeline_gate_summary.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows: list[PhaseStatus] = []

    rows.append(decision_gate_row(
        "manifest_init",
        "reports/physeditworld_50h/manifest_init/empty_manifest_init.json",
        READY_MANIFEST_INIT,
        "run expected-manifest initializer before any downstream gate",
        "check selected-root schema probe",
    ))
    rows.append(decision_gate_row(
        "root_schema_probe",
        "reports/migration/physeditworld_root_schema_probe.json",
        {READY_ROOT_SCHEMA_PROBE},
        "set PHYS_EDITWORLD_ROOTS to a selected root with action/camera/intrinsics/gravity/replay/video evidence",
        "check PAI/NAS and data readiness",
    ))
    if any(row.status == "BLOCKED" for row in rows):
        decision = pipeline_decision(rows)
        write_csv(rows, args.output_csv)
        write_json(rows, decision, args.output_json)
        write_summary(rows, decision, args.summary)
        print(json.dumps({"decision": decision, "phases": len(rows)}, sort_keys=True))
        return 0

    if args.run_readiness:
        code, out = run_command(["bash", "scripts/migration/check_physeditworld_pai_readiness.sh"], args.dry_run)
        if code != 0:
            rows.append(PhaseStatus("readiness", "READINESS_COMMAND_FAILED", "BLOCKED", "scripts/migration/check_physeditworld_pai_readiness.sh", error_reason=out))
        elif args.dry_run:
            rows.append(PhaseStatus("readiness", "READINESS_DRY_RUN_SKIPPED", "BLOCKED", "scripts/migration/check_physeditworld_pai_readiness.sh", next_action="rerun without --dry_run when checking live state"))

    if not any(row.phase == "readiness" for row in rows):
        decision, status, error = read_json_decision("reports/migration/physeditworld_pai_readiness.json")
        rows.append(PhaseStatus("readiness", decision, status, "reports/migration/physeditworld_pai_readiness.json", next_action="mount NAS and selected PhysEditWorld 50h root" if status == "BLOCKED" else "check migration asset validation", error_reason=error))

    asset_decision, asset_status, asset_error = read_json_decision("reports/migration/migration_asset_validation.json")
    rows.append(PhaseStatus("asset_validation", asset_decision, asset_status, "reports/migration/migration_asset_validation.json", next_action="mount NAS and rerun migration asset validation" if asset_status == "BLOCKED" else "check approved-only copy dry-run", error_reason=asset_error))

    copy_decision, copy_status, copy_error = read_json_decision("reports/migration/approved_copy_status.json")
    rows.append(PhaseStatus("approved_copy", copy_decision, copy_status, "reports/migration/approved_copy_status.json", next_action="approve required restore rows and rerun approved-copy dry-run" if copy_status == "BLOCKED" else "run baseline gate", error_reason=copy_error))

    if (
        any(row.phase == "readiness" and row.decision != READY_READINESS for row in rows)
        or asset_decision != READY_ASSET_VALIDATION
        or copy_decision not in READY_APPROVED_COPY
    ):
        decision = pipeline_decision(rows)
        write_csv(rows, args.output_csv)
        write_json(rows, decision, args.output_json)
        write_summary(rows, decision, args.summary)
        print(json.dumps({"decision": decision, "phases": len(rows)}, sort_keys=True))
        return 0

    for phase, path, reader, next_action in [
        ("baseline", "reports/physeditworld_50h_baseline_rollout/summary.md", read_md_decision, "run rank32 warm-up preflight"),
        ("warmup_preflight", "reports/physeditworld_50h_warmup_rank32/preflight_summary.md", read_md_decision, "run checkpoint eval gate"),
        ("checkpoint_eval", "reports/physeditworld_50h_warmup_rank32/best_checkpoint_decision.json", read_json_decision, "build anchored pairs"),
        ("pair_builder", "reports/physeditworld_dpo_pairs_anchored_v0/pair_summary.md", read_md_decision, "run tiny anchored DPO gate"),
        ("tiny_dpo", "reports/physeditworld_tiny_dpo_v0/best_checkpoint_decision.json", read_json_decision, "final decision"),
    ]:
        decision, status, error = reader(path)
        rows.append(PhaseStatus(phase, decision, status, path, next_action=next_action if status != "BLOCKED" else "resolve blocker before continuing", error_reason=error))
        if status == "BLOCKED" or "BLOCKED" in decision or decision == "MISSING":
            break

    decision = pipeline_decision(rows)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json)
    write_summary(rows, decision, args.summary)
    print(json.dumps({"decision": decision, "phases": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
