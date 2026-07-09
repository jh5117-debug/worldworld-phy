from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORTS = (
    ("root_template", "reports/migration/physeditworld_root_submission_template.json"),
    ("root_validation", "reports/migration/physeditworld_root_submission_validation.json"),
    ("root_evidence_samples", "reports/migration/physeditworld_root_evidence_samples.json"),
    ("root_onboarding", "reports/migration/physeditworld_root_onboarding_sequence.json"),
    ("external_state_watch", "reports/migration/physeditworld_external_state_watch.json"),
    ("root_candidates", "reports/migration/physeditworld_root_candidates_ranked.json"),
    ("root_schema_probe", "reports/migration/physeditworld_root_schema_probe.json"),
    ("root_selection", "reports/migration/physeditworld_selected_root_status.json"),
    ("requirement_matrix", "reports/physeditworld_50h/requirement_matrix.json"),
    ("completion_audit", "reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json"),
)

READY_ONBOARD = "PHYS_EDITWORLD_ROOT_ONBOARDING_READY_FOR_SCHEMA_PROBE"
WAIT_ONBOARD = "PHYS_EDITWORLD_ROOT_ONBOARDING_WAITING_FOR_FILLED_TEMPLATE"


@dataclass
class PacketRow:
    name: str
    path: str
    exists: bool
    decision: str
    next_action: str = ""
    error_reason: str = ""


def read_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"decision": "MISSING"}
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"decision": "UNREADABLE", "error_reason": repr(exc)}
    return obj if isinstance(obj, dict) else {"decision": "UNEXPECTED_JSON"}


def decision_of(obj: dict[str, Any]) -> str:
    return str(obj.get("decision") or obj.get("status") or "UNKNOWN")


def next_action(name: str, decision: str) -> str:
    if name == "external_state_watch" and "WAITING_FOR_NAS" in decision:
        return "mount or expose /mnt/workspace/hj/nas_hj before PAI handoff"
    if name == "external_state_watch" and "WAITING_FOR_ROOT_ENV" in decision:
        return "export PHYS_EDITWORLD_ROOTS to the selected PhysEditWorld 50h root"
    if decision == READY_ONBOARD:
        return "set PHYS_EDITWORLD_ROOTS and run selected-root/schema/locked handoff sequence"
    if decision == WAIT_ONBOARD:
        return "fill reports/migration/physeditworld_root_submission_template.tsv with selected 50h root and evidence globs"
    if name == "root_template" and decision == "PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY":
        return "send TSV to data owner or fill it with selected-root evidence"
    if "WAITING" in decision:
        return "fill the selected-root submission TSV"
    if "MISSING" in decision:
        return "run the corresponding report writer"
    if "BLOCKED" in decision or "REQUIRED" in decision:
        return "fix the blocker recorded in the report"
    return "continue to the next root onboarding gate"


def collect_rows() -> list[PacketRow]:
    rows: list[PacketRow] = []
    for name, path in REPORTS:
        obj = read_json(path)
        decision = decision_of(obj)
        rows.append(PacketRow(name, path, Path(path).exists(), decision, next_action(name, decision), str(obj.get("error_reason", ""))))
    return rows


def derive_decision(rows: list[PacketRow]) -> str:
    decisions = {row.name: row.decision for row in rows}
    if decisions.get("root_onboarding") == READY_ONBOARD:
        return "PHYS_EDITWORLD_EXTERNAL_ROOT_HANDOFF_READY_FOR_SCHEMA_PROBE"
    if decisions.get("root_onboarding") == WAIT_ONBOARD:
        return "PHYS_EDITWORLD_EXTERNAL_ROOT_HANDOFF_WAITING_FOR_FILLED_TEMPLATE"
    if any(row.decision in {"MISSING", "UNREADABLE", "UNEXPECTED_JSON"} for row in rows[:4]):
        return "PHYS_EDITWORLD_EXTERNAL_ROOT_HANDOFF_MISSING_ONBOARDING_REPORTS"
    return "PHYS_EDITWORLD_EXTERNAL_ROOT_HANDOFF_BLOCKED"


def write_json(path: str | Path, decision: str, rows: list[PacketRow]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "reports": [asdict(row) for row in rows],
        "operator_commands": [
            "cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys",
            "bash scripts/migration/run_physeditworld_root_onboarding_sequence.sh",
            "# fill reports/migration/physeditworld_root_submission_template.tsv if the packet says WAITING_FOR_FILLED_TEMPLATE",
            "export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root",
            "bash scripts/migration/select_physeditworld_root.sh",
            "bash scripts/migration/probe_physeditworld_root_schema.sh",
            "bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh",
        ],
        "safety": {
            "mode": "CPU/IO only",
            "does_not_copy_delete_train_or_use_gpu": True,
            "does_not_select_or_lock_root": True,
            "does_not_overwrite_existing_template_tsv": True,
        },
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: str | Path, decision: str, rows: list[PacketRow]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# PhysEditWorld External Root Handoff Packet", "", f"Decision: `{decision}`", "", "## Operator Summary", ""]
    if decision == "PHYS_EDITWORLD_EXTERNAL_ROOT_HANDOFF_WAITING_FOR_FILLED_TEMPLATE":
        lines.append("The onboarding toolchain is ready, but the selected-root TSV still contains placeholders. Fill the TSV with the real PhysEditWorld selected 50h root plus bounded action/camera/intrinsics/gravity/replay/video evidence globs.")
    elif decision == "PHYS_EDITWORLD_EXTERNAL_ROOT_HANDOFF_READY_FOR_SCHEMA_PROBE":
        lines.append("A submitted root has validation and evidence samples. Proceed to PHYS_EDITWORLD_ROOTS, root selection, schema probe, and locked handoff.")
    else:
        lines.append("Inspect the rows below and fix missing or blocked onboarding reports before root selection.")
    lines.extend(["", "## Report Decisions", ""])
    for row in rows:
        lines.append(f"- `{row.name}`: `{row.decision}`")
        lines.append(f"  - path: `{row.path}`")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
        if row.error_reason:
            lines.append(f"  - error: {row.error_reason}")
    lines.extend([
        "", "## Commands", "", "```bash",
        "cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys",
        "bash scripts/migration/run_physeditworld_root_onboarding_sequence.sh",
        "# Fill reports/migration/physeditworld_root_submission_template.tsv if still waiting.",
        "export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root",
        "bash scripts/migration/select_physeditworld_root.sh",
        "bash scripts/migration/probe_physeditworld_root_schema.sh",
        "bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh",
        "```",
        "", "## Safety", "",
        "This packet is CPU/IO only. It reads existing JSON reports and writes a lightweight operator packet. It does not copy files, delete files, use GPUs, train, rollout, run DPO, or select/lock a root.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Write an external operator packet for PhysEditWorld selected-root onboarding")
    ap.add_argument("--output_json", default="reports/migration/physeditworld_external_root_handoff_packet.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_external_root_handoff_packet.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = collect_rows()
    decision = derive_decision(rows)
    write_json(args.output_json, decision, rows)
    write_markdown(args.summary, decision, rows)
    print(json.dumps({"decision": decision, "reports": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
