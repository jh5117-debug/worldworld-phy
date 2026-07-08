from __future__ import annotations

import argparse
import csv
import json
import shlex
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class PreflightStep:
    step: str
    command: str
    exit_code: int
    decision: str
    status: str
    evidence: str
    error_reason: str = ""


PASS_DECISIONS = {
    "PHYS_EDITWORLD_EMPTY_MANIFESTS_INITIALIZED",
    "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT",
    "MIGRATION_AUDIT_BUNDLE_READY",
    "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT",
    "MIGRATION_ASSET_VALIDATION_PASS",
    "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG",
    "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT",
    "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED",
    "PHYS_EDITWORLD_ROOT_INTAKE_LOCKED_READY_FOR_HANDOFF",
    "LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE",
    "PAI_HANDOFF_READY_FOR_POST_MOUNT_CONTINUE",
    "APPROVED_COPY_DRYRUN_READY",
    "APPROVED_COPY_EXECUTED",
    "PHYS_EDIT_WORLD_PIPELINE_REQUIREMENTS_PASS",
    "PIPELINE_READY_FOR_NEXT_EXECUTION_STEP",
    "PHYS_EDITWORLD_BACKEND_READY_FOR_BASELINE_WARMUP",
    "PHYS_EDITWORLD_EXTERNAL_UNBLOCK_PACKET_READY_FOR_POST_MOUNT",
}

REVIEW_DECISIONS = {
    "COPY_PLAN_REVIEW_REQUIRED",
    "COPY_PLAN_READY_FOR_APPROVAL",
}


def read_decision(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return "MISSING"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        return str(obj.get("decision") or obj.get("status") or "UNKNOWN")
    except Exception:
        return "UNREADABLE"


def status_for(decision: str, exit_code: int) -> str:
    if exit_code != 0:
        return "FAIL"
    if decision in PASS_DECISIONS:
        return "PASS"
    if decision in REVIEW_DECISIONS:
        return "REVIEW_REQUIRED"
    if (
        "BLOCKED" in decision
        or "WAITING" in decision
        or "WEAK_ONLY" in decision
        or "NONE_STRONG" in decision
        or "UNBLOCK_REQUIRED" in decision
        or "REQUIRED_NAS_OR_ROOT" in decision
        or decision.endswith("_EMPTY")
        or decision in {"MISSING", "UNREADABLE"}
    ):
        return "BLOCKED"
    if "REVIEW_REQUIRED" in decision:
        return "REVIEW_REQUIRED"
    return "UNKNOWN"


def run_command(cmd: list[str], evidence: str, dry_run: bool) -> PreflightStep:
    printable = " ".join(shlex.quote(x) for x in cmd)
    if dry_run:
        decision = read_decision(evidence)
        return PreflightStep(Path(evidence).stem, "DRY_RUN " + printable, 0, decision, status_for(decision, 0), evidence)
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    decision = read_decision(evidence)
    return PreflightStep(Path(evidence).stem, printable, proc.returncode, decision, status_for(decision, proc.returncode), evidence, "" if proc.returncode == 0 else proc.stdout[-2000:])


def overall_decision(rows: list[PreflightStep]) -> str:
    order = [
        ("empty_manifest_init", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_MANIFEST_INIT"),
        ("migration_audit_bundle", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_MIGRATION_AUDIT"),
        ("physeditworld_root_candidates_ranked", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_ROOT_CANDIDATES"),
        ("physeditworld_root_schema_probe", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_ROOT_SCHEMA_PROBE"),
        ("physeditworld_selected_root_status", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_ROOT_SELECTION"),
        ("physeditworld_root_intake", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_ROOT_INTAKE"),
        ("locked_handoff_sequence", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_LOCKED_HANDOFF"),
        ("physeditworld_pai_readiness", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_READINESS"),
        ("migration_asset_validation", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_ASSET_VALIDATION"),
        ("approved_copy_manifest_template", "PHYS_EDITWORLD_PHASE0_REVIEW_COPY_PLAN"),
        ("approved_copy_status", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_APPROVED_COPY"),
        ("pai_handoff_status", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_PAI_HANDOFF"),
        ("backend_readiness", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_BACKEND_READINESS"),
        ("requirement_matrix", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_REQUIREMENT_MATRIX"),
        ("pipeline_gate_status", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_PIPELINE_GATE"),
        ("physeditworld_external_unblock_packet", "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_EXTERNAL_UNBLOCK_PACKET"),
    ]
    by_step = {row.step: row for row in rows}
    for step, decision in order:
        row = by_step.get(step)
        if not row:
            return "PHYS_EDITWORLD_PHASE0_PREFLIGHT_INCOMPLETE"
        if row.status == "BLOCKED" or row.status == "FAIL":
            return decision
        if row.status == "REVIEW_REQUIRED" and step != "approved_copy_manifest_template":
            return decision
    if any(row.status == "REVIEW_REQUIRED" for row in rows):
        return "PHYS_EDITWORLD_PHASE0_REVIEW_REQUIRED"
    if all(row.status == "PASS" for row in rows):
        return "PHYS_EDITWORLD_PHASE0_READY"
    return "PHYS_EDITWORLD_PHASE0_UNKNOWN"


def write_csv(rows: list[PreflightStep], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(PreflightStep.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[PreflightStep], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "steps": [asdict(row) for row in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[PreflightStep], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# PhysEditWorld Phase 0 Migration Preflight", "", f"Decision: `{decision}`", "", "## Steps", ""]
    for row in rows:
        lines.append(f"- `{row.step}`: `{row.status}` / `{row.decision}`")
        lines.append(f"  - evidence: `{row.evidence}`")
        lines.append(f"  - command: `{row.command}`")
        if row.error_reason:
            lines.append(f"  - error: {row.error_reason}")
    lines.extend([
        "",
        "## Safety",
        "",
        "- This preflight does not run rsync execute.",
        "- It does not pass `--execute` to the approved-copy tool.",
        "- It does not copy data, weights, checkpoints, videos, or local_assets.",
        "- It does not delete files and does not use GPUs.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run safe Phase 0 migration preflight for PhysEditWorld")
    ap.add_argument("--dry_run", action="store_true")
    ap.add_argument("--output_csv", default="reports/migration/phase0_preflight_status.csv")
    ap.add_argument("--output_json", default="reports/migration/phase0_preflight_status.json")
    ap.add_argument("--summary", default="reports/migration/phase0_preflight_summary.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    commands = [
        (["bash", "scripts/migration/init_physeditworld_empty_manifests.sh"], "reports/physeditworld_50h/manifest_init/empty_manifest_init.json"),
        (["bash", "scripts/migration/collect_physeditworld_migration_audit_bundle.sh"], "reports/migration/migration_audit_bundle.json"),
        (["bash", "scripts/migration/rank_physeditworld_root_candidates.sh"], "reports/migration/physeditworld_root_candidates_ranked.json"),
        (["bash", "scripts/migration/probe_physeditworld_root_schema.sh"], "reports/migration/physeditworld_root_schema_probe.json"),
        (["bash", "scripts/migration/select_physeditworld_root.sh"], "reports/migration/physeditworld_selected_root_status.json"),
        (["bash", "scripts/migration/prepare_physeditworld_root_intake.sh"], "reports/migration/physeditworld_root_intake.json"),
        (["bash", "scripts/migration/run_physeditworld_locked_handoff_sequence.sh"], "reports/migration/locked_handoff_sequence.json"),
        (["bash", "scripts/migration/check_physeditworld_pai_readiness.sh"], "reports/migration/physeditworld_pai_readiness.json"),
        (["bash", "scripts/migration/validate_physeditworld_migration_assets.sh"], "reports/migration/migration_asset_validation.json"),
        (["bash", "scripts/migration/build_physeditworld_migration_copy_plan.sh"], "reports/migration/approved_copy_manifest_template.json"),
        (["bash", "scripts/migration/run_approved_migration_copy.sh"], "reports/migration/approved_copy_status.json"),
        (["bash", "scripts/migration/verify_pai_physeditworld_handoff.sh"], "reports/migration/pai_handoff_status.json"),
        (["python3", "-m", "cam_physgeo.orchestration.physeditworld_backend_readiness"], "reports/physeditworld_50h/backend_readiness/backend_readiness.json"),
        (["python3", "-m", "cam_physgeo.orchestration.physeditworld_requirement_matrix"], "reports/physeditworld_50h/requirement_matrix.json"),
        (["python3", "-m", "cam_physgeo.orchestration.physeditworld_pipeline_gate"], "reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json"),
        (["bash", "scripts/migration/write_physeditworld_external_unblock_packet.sh"], "reports/migration/physeditworld_external_unblock_packet.json"),
    ]
    rows = [run_command(cmd, evidence, args.dry_run) for cmd, evidence in commands]
    decision = overall_decision(rows)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json)
    write_summary(rows, decision, args.summary)
    print(json.dumps({"decision": decision, "steps": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
