from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class SequenceStep:
    step: str
    status: str
    command: str
    evidence: str
    decision: str = ""
    exit_code: int | None = None
    error_reason: str = ""
    next_action: str = ""


PASS_DECISIONS = {
    "PHYS_EDITWORLD_EMPTY_MANIFESTS_INITIALIZED",
    "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT",
    "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED",
    "POST_MOUNT_PHASE12_DONE_RUN_PIPELINE_GATE_NEXT",
    "PHYS_EDITWORLD_PHASE0_READY",
    "PAI_HANDOFF_READY_FOR_POST_MOUNT_CONTINUE",
    "PIPELINE_READY_FOR_NEXT_EXECUTION_STEP",
    "PHYS_EDIT_WORLD_PIPELINE_REQUIREMENTS_PASS",
}

REVIEW_DECISIONS = {
    "PHYS_EDITWORLD_PHASE0_REVIEW_REQUIRED",
}


STEP_SPECS = [
    (
        "empty_manifest_init",
        ["bash", "scripts/migration/init_physeditworld_empty_manifests.sh"],
        "reports/physeditworld_50h/manifest_init/empty_manifest_init.json",
        "create expected lightweight manifest placeholders before root-locked handoff",
    ),
    (
        "root_selection",
        ["bash", "scripts/migration/select_physeditworld_root.sh"],
        "reports/migration/physeditworld_selected_root_status.json",
        "set PHYS_EDITWORLD_ROOTS to a strong selected PhysEditWorld 50h root",
    ),
    (
        "post_mount",
        ["bash", "scripts/continue_physeditworld_after_mount.sh"],
        "reports/physeditworld_50h/post_mount/post_mount_status.json",
        "resolve root-lock/data manifest blocker before post-mount continuation",
    ),
    (
        "phase0_preflight",
        ["bash", "scripts/migration/run_physeditworld_phase0_preflight.sh"],
        "reports/migration/phase0_preflight_status.json",
        "resolve migration/NAS/copy-plan blockers",
    ),
    (
        "pai_handoff",
        ["bash", "scripts/migration/verify_pai_physeditworld_handoff.sh"],
        "reports/migration/pai_handoff_status.json",
        "mount NAS/root and rerun handoff verification",
    ),
    (
        "pipeline_gate",
        ["bash", "scripts/run_physeditworld_pipeline_gates.sh"],
        "reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json",
        "resolve first blocked pipeline phase before training or rollout",
    ),
    (
        "requirement_matrix",
        ["python3", "-m", "cam_physgeo.orchestration.physeditworld_requirement_matrix"],
        "reports/physeditworld_50h/requirement_matrix.json",
        "resolve missing or blocked requirement rows",
    ),
]


def read_decision(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return "MISSING"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return "UNREADABLE:" + repr(exc)
    return str(obj.get("decision") or obj.get("status") or "UNKNOWN")


def status_for_decision(decision: str, exit_code: int) -> str:
    if exit_code != 0:
        return "FAIL"
    if decision in PASS_DECISIONS:
        return "PASS"
    if decision in REVIEW_DECISIONS:
        return "REVIEW_REQUIRED"
    if decision == "MISSING" or decision.startswith("UNREADABLE"):
        return "BLOCKED"
    if "BLOCKED" in decision or "FAIL" in decision or "WEAK_ONLY" in decision or "NONE_STRONG" in decision:
        return "BLOCKED"
    return "UNKNOWN"


def run_command(cmd: list[str], evidence: str, next_action: str, dry_run: bool) -> SequenceStep:
    printable = " ".join(shlex.quote(x) for x in cmd)
    if dry_run:
        decision = read_decision(evidence)
        return SequenceStep(
            step=Path(evidence).stem,
            status=status_for_decision(decision, 0),
            command="DRY_RUN " + printable,
            evidence=evidence,
            decision=decision,
            exit_code=0,
            next_action=next_action,
        )
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    decision = read_decision(evidence)
    status = status_for_decision(decision, proc.returncode)
    return SequenceStep(
        step=Path(evidence).stem,
        status=status,
        command=printable,
        evidence=evidence,
        decision=decision,
        exit_code=proc.returncode,
        error_reason="" if proc.returncode == 0 else proc.stdout[-3000:],
        next_action="" if status == "PASS" else next_action,
    )


def overall_decision(rows: Iterable[SequenceStep]) -> str:
    rows = list(rows)
    if not rows:
        return "LOCKED_HANDOFF_NO_STEPS"
    first_bad = next((row for row in rows if row.status in {"BLOCKED", "FAIL", "UNKNOWN"}), None)
    if first_bad:
        return "LOCKED_HANDOFF_BLOCKED_AT_" + first_bad.step.upper()
    if any(row.status == "REVIEW_REQUIRED" for row in rows):
        return "LOCKED_HANDOFF_REVIEW_REQUIRED"
    return "LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE"


def write_csv(rows: list[SequenceStep], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(SequenceStep.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[SequenceStep], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "steps": [asdict(row) for row in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[SequenceStep], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# PhysEditWorld Locked Handoff Sequence", "", f"Decision: `{decision}`", "", "## Steps", ""]
    for row in rows:
        lines.append(f"- `{row.step}`: `{row.status}` / `{row.decision}`")
        lines.append(f"  - command: `{row.command}`")
        lines.append(f"  - evidence: `{row.evidence}`")
        if row.error_reason:
            lines.append(f"  - error: {row.error_reason}")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    lines.extend([
        "",
        "## Safety",
        "",
        "This sequence is CPU/IO only. It locks a strong selected root before post-mount work, then refreshes Phase0, handoff, pipeline, and requirement reports.",
        "It does not copy files, delete files, use GPUs, train, rollout, run DPO, or push large artifacts.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run root-locked PhysEditWorld post-mount handoff sequence")
    ap.add_argument("--dry_run", action="store_true")
    ap.add_argument("--continue_on_blocked", action="store_true", help="Run all steps for report refresh even after a blocked step.")
    ap.add_argument("--output_csv", default="reports/migration/locked_handoff_sequence.csv")
    ap.add_argument("--output_json", default="reports/migration/locked_handoff_sequence.json")
    ap.add_argument("--summary", default="reports/migration/locked_handoff_sequence.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows: list[SequenceStep] = []
    for name, cmd, evidence, next_action in STEP_SPECS:
        row = run_command(cmd, evidence, next_action, args.dry_run)
        row.step = name
        rows.append(row)
        if row.status in {"BLOCKED", "FAIL", "UNKNOWN"} and not args.continue_on_blocked:
            break
    decision = overall_decision(rows)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json)
    write_summary(rows, decision, args.summary)
    print(json.dumps({"decision": decision, "steps": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
