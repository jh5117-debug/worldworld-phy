from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

READY_VALIDATION = "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_READY_FOR_SCHEMA_PROBE"
READY_SAMPLER = "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_READY_FOR_SCHEMA_PROBE"
WAIT_VALIDATION = "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE"
WAIT_SAMPLER = "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE"
TEMPLATE_READY = "PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY"

@dataclass
class OnboardingStep:
    name: str
    status: str
    decision: str
    path: str
    detail: str = ""
    next_action: str = ""
    error_reason: str = ""

def run_module(module: str, timeout_seconds: int) -> tuple[int, str]:
    try:
        proc = subprocess.run(["python3", "-m", module], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False, timeout=timeout_seconds)
    except Exception as exc:
        return 124, repr(exc)
    return proc.returncode, proc.stdout.strip()

def read_decision(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return "MISSING"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return "UNREADABLE:" + repr(exc)
    return str(obj.get("decision") or obj.get("status") or "UNKNOWN")

def next_action_for_decision(decision: str) -> str:
    if decision in {READY_VALIDATION, READY_SAMPLER}:
        return "set PHYS_EDITWORLD_ROOTS to the ready candidate root, then run select/probe/locked handoff"
    if decision in {WAIT_VALIDATION, WAIT_SAMPLER}:
        return "fill reports/migration/physeditworld_root_submission_template.tsv with the selected 50h root and bounded evidence globs"
    if "ROOT_NOT_VISIBLE" in decision:
        return "mount or expose the submitted root on H20/PAI"
    if "INCOMPLETE" in decision or "BLOCKED" in decision:
        return "fix candidate_root/evidence globs before schema probe"
    if decision == "MISSING":
        return "run the missing prior report writer"
    return "inspect the report and fix the reported blocker"

def maybe_generate_reports(args: argparse.Namespace) -> list[OnboardingStep]:
    steps: list[OnboardingStep] = []
    if not Path(args.template_tsv).exists():
        code, out = run_module("cam_physgeo.orchestration.physeditworld_root_submission_template", args.timeout_seconds)
        status = "PASS" if code == 0 else "BLOCKED"
        steps.append(OnboardingStep("write_template_if_missing", status, read_decision(args.template_json), args.template_json, out[-500:], "fill the TSV with the selected 50h root" if status == "PASS" else "fix template writer", "" if code == 0 else out[-500:]))
    else:
        steps.append(OnboardingStep("write_template_if_missing", "PASS", read_decision(args.template_json), args.template_json, "template TSV already exists; not overwritten", "fill TSV if still placeholder"))
    for name, module, report in [
        ("validate_submission", "cam_physgeo.orchestration.physeditworld_root_submission_validate", args.validation_json),
        ("sample_evidence", "cam_physgeo.orchestration.physeditworld_root_evidence_sampler", args.sampler_json),
    ]:
        code, out = run_module(module, args.timeout_seconds)
        decision = read_decision(report)
        status = "PASS" if code == 0 and decision in {READY_VALIDATION, READY_SAMPLER, WAIT_VALIDATION, WAIT_SAMPLER} else "BLOCKED"
        steps.append(OnboardingStep(name, status, decision, report, out[-500:], next_action_for_decision(decision), "" if code == 0 else out[-500:]))
    return steps

def derive_decision(steps: list[OnboardingStep]) -> str:
    decisions = {step.name: step.decision for step in steps}
    if decisions.get("validate_submission") == READY_VALIDATION and decisions.get("sample_evidence") == READY_SAMPLER:
        return "PHYS_EDITWORLD_ROOT_ONBOARDING_READY_FOR_SCHEMA_PROBE"
    if decisions.get("validate_submission") == WAIT_VALIDATION or decisions.get("sample_evidence") == WAIT_SAMPLER:
        return "PHYS_EDITWORLD_ROOT_ONBOARDING_WAITING_FOR_FILLED_TEMPLATE"
    if any(step.status == "BLOCKED" for step in steps):
        return "PHYS_EDITWORLD_ROOT_ONBOARDING_BLOCKED"
    return "PHYS_EDITWORLD_ROOT_ONBOARDING_INCOMPLETE"

def write_json(path: str | Path, decision: str, steps: list[OnboardingStep]) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "steps": [asdict(step) for step in steps],
        "safe_next_commands": [
            "bash scripts/migration/write_physeditworld_root_submission_template.sh  # only if template is missing",
            "bash scripts/migration/validate_physeditworld_root_submission.sh",
            "bash scripts/migration/sample_physeditworld_root_evidence.sh",
            "export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root",
            "bash scripts/migration/select_physeditworld_root.sh",
            "bash scripts/migration/probe_physeditworld_root_schema.sh",
            "bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh",
        ],
        "safety": {"mode": "CPU/IO only", "does_not_overwrite_existing_template_tsv": True, "does_not_copy_delete_train_or_use_gpu": True, "does_not_select_or_lock_root": True},
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def write_markdown(path: str | Path, decision: str, steps: list[OnboardingStep]) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# PhysEditWorld Root Onboarding Sequence", "", f"Decision: `{decision}`", "", "## Steps", ""]
    for step in steps:
        lines.append(f"- `{step.name}`: `{step.status}` / `{step.decision}`")
        lines.append(f"  - report: `{step.path}`")
        if step.detail:
            lines.append(f"  - detail: {step.detail}")
        if step.next_action:
            lines.append(f"  - next: {step.next_action}")
        if step.error_reason:
            lines.append(f"  - error: {step.error_reason}")
    lines.extend(["", "## Safe Resume Commands", "", "```bash", "cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys", "bash scripts/migration/run_physeditworld_root_onboarding_sequence.sh", "export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root", "bash scripts/migration/select_physeditworld_root.sh", "bash scripts/migration/probe_physeditworld_root_schema.sh", "bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh", "```", "", "## Safety", "", "This sequence is CPU/IO only. It does not overwrite an existing filled TSV, copy files, delete files, approve migration rows, select/lock a root, use GPUs, train, rollout, evaluate videos, or run DPO."])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run the CPU-only PhysEditWorld selected-root onboarding sequence")
    ap.add_argument("--template_tsv", default="reports/migration/physeditworld_root_submission_template.tsv")
    ap.add_argument("--template_json", default="reports/migration/physeditworld_root_submission_template.json")
    ap.add_argument("--validation_json", default="reports/migration/physeditworld_root_submission_validation.json")
    ap.add_argument("--sampler_json", default="reports/migration/physeditworld_root_evidence_samples.json")
    ap.add_argument("--output_json", default="reports/migration/physeditworld_root_onboarding_sequence.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_root_onboarding_sequence.md")
    ap.add_argument("--timeout_seconds", type=int, default=120)
    return ap

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    steps = maybe_generate_reports(args)
    decision = derive_decision(steps)
    write_json(args.output_json, decision, steps)
    write_markdown(args.summary, decision, steps)
    print(json.dumps({"decision": decision, "steps": len(steps)}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
