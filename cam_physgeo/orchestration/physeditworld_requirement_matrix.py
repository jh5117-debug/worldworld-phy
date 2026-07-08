from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class RequirementRow:
    phase: str
    requirement: str
    status: str
    evidence: str
    detail: str = ""
    next_action: str = ""


PHASE0_DECISION_GATES = [
    (
        "reports/physeditworld_50h/manifest_init/empty_manifest_init.json",
        "expected empty manifest placeholders",
        {"PHYS_EDITWORLD_EMPTY_MANIFESTS_INITIALIZED", "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT"},
        "run expected-manifest initializer before any post-mount work",
    ),
    (
        "reports/migration/physeditworld_pai_readiness.json",
        "PAI/NAS and data readiness",
        {"READY_FOR_BASELINE_ROLLOUT_PREFLIGHT"},
        "mount NAS and selected PhysEditWorld 50h root",
    ),
    (
        "reports/migration/physeditworld_root_candidates_ranked.json",
        "PhysEditWorld root candidate ranking",
        {"PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG"},
        "provide selected PhysEditWorld root via PHYS_EDITWORLD_ROOTS and rerun root candidate ranker",
    ),
    (
        "reports/migration/physeditworld_root_schema_probe.json",
        "selected-root schema probe",
        {"PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"},
        "provide a selected root with action/camera/intrinsics/gravity/replay/video evidence and rerun schema probe",
    ),
    (
        "reports/migration/physeditworld_selected_root_status.json",
        "PhysEditWorld selected-root lock",
        {"PHYS_EDITWORLD_ROOT_SELECTION_LOCKED"},
        "set PHYS_EDITWORLD_ROOTS to a strong root and rerun selected-root verifier",
    ),
    (
        "reports/migration/locked_handoff_sequence.json",
        "locked handoff sequence",
        {"LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE"},
        "rerun locked handoff after NAS/root/schema gates are satisfied",
    ),
    (
        "reports/migration/migration_asset_validation.json",
        "migration asset validation",
        {"MIGRATION_ASSET_VALIDATION_PASS"},
        "mount NAS and rerun migration asset validation before execute copy",
    ),
    (
        "reports/migration/approved_copy_status.json",
        "approved-only copy executor status",
        {"APPROVED_COPY_DRYRUN_READY", "APPROVED_COPY_EXECUTED"},
        "mark required restore rows approved=true and rerun approved-copy dry-run after NAS is visible",
    ),
    (
        "reports/migration/pai_handoff_status.json",
        "PAI handoff verifier",
        {"PAI_HANDOFF_READY_FOR_POST_MOUNT_CONTINUE"},
        "mount NAS/PhysEditWorld root and rerun PAI handoff verifier",
    ),
]


def count_jsonl(path: str | Path) -> int | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def read_json_decision(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return "MISSING"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        return str(obj.get("decision") or obj.get("status") or "UNKNOWN")
    except Exception:
        return "UNREADABLE"


def read_md_decision(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return "MISSING"
    text = p.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        if line.strip().lower().startswith("decision:"):
            if "`" in line:
                parts = line.split("`")
                if len(parts) >= 2:
                    return parts[1].strip()
            return line.split(":", 1)[1].strip()
    return "UNKNOWN"


def file_status(path: str | Path, requirement: str, phase: str, next_action: str = "") -> RequirementRow:
    p = Path(path)
    if p.exists():
        return RequirementRow(phase, requirement, "PASS", str(p), detail="file exists")
    return RequirementRow(phase, requirement, "MISSING", str(p), detail="file missing", next_action=next_action)


def manifest_status(path: str | Path, requirement: str, phase: str, min_rows: int, next_action: str) -> RequirementRow:
    rows = count_jsonl(path)
    if rows is None:
        return RequirementRow(phase, requirement, "MISSING", str(path), detail="manifest missing", next_action=next_action)
    if rows < min_rows:
        return RequirementRow(phase, requirement, "BLOCKED", str(path), detail=f"rows={rows}, required>={min_rows}", next_action=next_action)
    return RequirementRow(phase, requirement, "PASS", str(path), detail=f"rows={rows}")


def decision_status(path: str | Path, requirement: str, phase: str, pass_values: set[str], next_action: str) -> RequirementRow:
    decision = read_json_decision(path)
    if decision in pass_values:
        status = "PASS"
    elif decision == "MISSING":
        status = "MISSING"
    else:
        status = "BLOCKED"
    return RequirementRow(phase, requirement, status, str(path), detail=f"decision={decision}", next_action="" if status == "PASS" else next_action)


def md_decision_status(path: str | Path, requirement: str, phase: str, pass_values: set[str], next_action: str) -> RequirementRow:
    decision = read_md_decision(path)
    if decision in pass_values:
        status = "PASS"
    elif decision == "MISSING":
        status = "MISSING"
    else:
        status = "BLOCKED"
    return RequirementRow(phase, requirement, status, str(path), detail=f"decision={decision}", next_action="" if status == "PASS" else next_action)


def build_rows() -> list[RequirementRow]:
    rows: list[RequirementRow] = []
    rows.extend([
        file_status("docs/experiments/EXP_physeditworld_50h_prompt_gravity_lingbotfast.md", "PRD exists", "0_prd", "write PRD"),
        file_status("docs/physeditworld_50h_current_status.md", "status doc exists", "0_prd", "write status"),
        file_status("reports/migration/environment_no_builds.yml", "environment export", "0_migration", "export conda env"),
        file_status("reports/migration/pip_freeze.txt", "pip freeze export", "0_migration", "export pip freeze"),
        file_status("reports/migration/required_weights_manifest.tsv", "required weights manifest", "0_migration", "build weights manifest"),
        file_status("reports/migration/required_data_manifest.tsv", "required data manifest", "0_migration", "build data manifest"),
        file_status("scripts/migration/rsync_h20_to_pai_dryrun.sh", "rsync dry-run script", "0_migration", "add dry-run script"),
        file_status("scripts/migration/rsync_h20_to_pai_execute.sh", "guarded rsync execute script", "0_migration", "add execute script"),
        file_status("reports/migration/approved_copy_manifest_template.tsv", "explicit copy-plan template", "0_migration", "generate approved copy manifest template"),
    ])
    for evidence, requirement, pass_values, next_action in PHASE0_DECISION_GATES:
        rows.append(decision_status(evidence, requirement, "0_migration", pass_values, next_action))
    rows.extend([
        manifest_status("manifests/physeditworld_50h_all.jsonl", "strict selected 50h manifest", "1_data_audit", 1, "mount selected PhysEditWorld 50h root and rerun manifest audit"),
        manifest_status("manifests/physeditworld_50h_train.jsonl", "train split manifest", "1_data_audit", 1, "rerun replay-group split"),
        file_status("reports/physeditworld_50h/split_summary.md", "split summary", "1_data_audit", "run split summary"),
        decision_status("reports/physeditworld_50h/prompt_gravity_policy/prompt_gravity_policy_audit.json", "prompt-only gravity policy audit", "2_conversion", {"PHYS_EDITWORLD_PROMPT_GRAVITY_POLICY_PASS"}, "fix prompt-only gravity policy before conversion or warm-up"),
        manifest_status("manifests/physeditworld_50h_lingbot_train.jsonl", "LingBot train conversion manifest", "2_conversion", 1, "rerun prompt-only LingBot conversion"),
        manifest_status("manifests/physeditworld_50h_lingbot_val.jsonl", "LingBot val conversion manifest", "2_conversion", 1, "rerun prompt-only LingBot conversion"),
        decision_status(
            "reports/physeditworld_50h/conversion_validation/lingbot_train_manifest_validation.json",
            "LingBot train conversion schema validation",
            "2_conversion",
            {"LINGBOT_MANIFEST_SCHEMA_PASS"},
            "rerun conversion manifest validator after prompt-only LingBot conversion writes rows",
        ),
        decision_status(
            "reports/physeditworld_50h/conversion_validation/lingbot_val_manifest_validation.json",
            "LingBot val conversion schema validation",
            "2_conversion",
            {"LINGBOT_MANIFEST_SCHEMA_PASS"},
            "rerun conversion manifest validator after prompt-only LingBot conversion writes rows",
        ),
        md_decision_status("reports/physeditworld_50h_baseline_rollout/summary.md", "baseline true rollout gate", "3_baseline", {"BASELINE_ROLLOUT_PASS", "PROMPT_ONLY_GRAVITY_BASELINE_WEAK"}, "run true baseline rollout after LingBot manifests exist"),
        md_decision_status("reports/physeditworld_50h_warmup_rank32/preflight_summary.md", "rank32 warm-up preflight", "4_warmup", {"WARMUP_PREFLIGHT_PASS"}, "run 5-step rank32 warm-up preflight after conversion"),
        decision_status("reports/physeditworld_50h_warmup_rank32/best_checkpoint_decision.json", "checkpoint video/metric gate", "5_checkpoint_eval", {"WARMUP_GATE_PASS"}, "produce true rollout videos, metrics, and Codex audit"),
        decision_status("reports/physeditworld_tiny_dpo_v0/best_checkpoint_decision.json", "tiny anchored DPO gate", "7_tiny_dpo", {"TINY_DPO_PASS"}, "build >=100 reviewed pairs before tiny DPO"),
        file_status("docs/experiments/EXP_physeditworld50_plus_ourphysics50_ablation_plan.md", "future mixed-data ablation plan", "8_ablation", "write ablation plan"),
    ])
    pair_rows = count_jsonl("manifests/physeditworld_dpo_pairs_anchored_v0.jsonl")
    if pair_rows is None:
        rows.append(RequirementRow("6_pairs", "anchored DPO pair manifest", "MISSING", "manifests/physeditworld_dpo_pairs_anchored_v0.jsonl", "manifest missing", "run pair builder after warm-up gate"))
    elif pair_rows < 100:
        rows.append(RequirementRow("6_pairs", "anchored DPO pair manifest", "BLOCKED", "manifests/physeditworld_dpo_pairs_anchored_v0.jsonl", f"rows={pair_rows}, required>=100", "run pair builder after warm-up checkpoint gate passes"))
    else:
        rows.append(RequirementRow("6_pairs", "anchored DPO pair manifest", "PASS", "manifests/physeditworld_dpo_pairs_anchored_v0.jsonl", f"rows={pair_rows}"))
    return rows


def overall_decision(rows: list[RequirementRow]) -> str:
    if any(row.phase == "0_migration" and row.status != "PASS" for row in rows):
        return "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS"
    if any(row.phase == "1_data_audit" and row.status != "PASS" for row in rows):
        return "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_DATA_AUDIT"
    if any(row.phase == "2_conversion" and row.status != "PASS" for row in rows):
        return "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_CONVERSION"
    if any(row.phase == "3_baseline" and row.status != "PASS" for row in rows):
        return "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_BASELINE"
    if any(row.phase == "4_warmup" and row.status != "PASS" for row in rows):
        return "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_WARMUP_PREFLIGHT"
    if any(row.phase == "5_checkpoint_eval" and row.status != "PASS" for row in rows):
        return "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_CHECKPOINT_EVAL"
    if any(row.phase == "6_pairs" and row.status != "PASS" for row in rows):
        return "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_PAIR_GATE"
    if any(row.phase == "7_tiny_dpo" and row.status != "PASS" for row in rows):
        return "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_TINY_DPO"
    if any(row.status in {"BLOCKED", "MISSING"} for row in rows):
        return "PHYS_EDIT_WORLD_PIPELINE_PARTIAL"
    return "PHYS_EDIT_WORLD_PIPELINE_REQUIREMENTS_PASS"


def write_csv(rows: list[RequirementRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = ["phase", "requirement", "status", "evidence", "detail", "next_action"]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[RequirementRow], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "requirements": [asdict(row) for row in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[RequirementRow], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row.status] = by_status.get(row.status, 0) + 1
    lines = ["# PhysEditWorld Requirement Matrix", "", f"Decision: `{decision}`", "", "## Status Counts", ""]
    for key in sorted(by_status):
        lines.append(f"- `{key}`: {by_status[key]}")
    lines.extend(["", "## Requirements", ""])
    for row in rows:
        lines.append(f"- `{row.phase}` / {row.requirement}: `{row.status}`")
        lines.append(f"  - evidence: `{row.evidence}`")
        if row.detail:
            lines.append(f"  - detail: {row.detail}")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Generate PhysEditWorld objective requirement matrix")
    ap.add_argument("--output_csv", default="reports/physeditworld_50h/requirement_matrix.csv")
    ap.add_argument("--output_json", default="reports/physeditworld_50h/requirement_matrix.json")
    ap.add_argument("--summary", default="reports/physeditworld_50h/requirement_matrix.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = build_rows()
    decision = overall_decision(rows)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json)
    write_summary(rows, decision, args.summary)
    print(json.dumps({"decision": decision, "requirements": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
