from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


FORBIDDEN_RE = re.compile(
    r"(^local_assets/|\.(mp4|jpg|jpeg|png|hdf5|h5|npy|npz|pt|pth|safetensors|ckpt|bin|tar|zip|log)$)",
    re.IGNORECASE,
)


@dataclass
class AuditRow:
    phase: str
    requirement: str
    status: str
    evidence: str
    detail: str = ""
    next_action: str = ""


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
    except Exception as exc:
        return "UNREADABLE:" + repr(exc)
    return str(obj.get("decision") or obj.get("status") or "UNKNOWN")


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


def status_from_decision(decision: str, pass_values: set[str]) -> str:
    if decision in pass_values:
        return "PASS"
    if decision == "MISSING" or decision.startswith("UNREADABLE"):
        return "MISSING"
    if (
        "BLOCKED" in decision
        or "FAIL" in decision
        or "NOT_FOUND" in decision
        or "MISSING" in decision
        or "WAITING" in decision
        or "NEED" in decision
        or "REQUIRED" in decision
        or "INCOMPLETE" in decision
    ):
        return "BLOCKED"
    if "PASS" in decision or "READY" in decision:
        return "PARTIAL"
    return "UNKNOWN"


def file_row(phase: str, requirement: str, path: str, next_action: str = "") -> AuditRow:
    p = Path(path)
    if p.exists():
        return AuditRow(phase, requirement, "PASS", path, "file exists")
    return AuditRow(phase, requirement, "MISSING", path, "file missing", next_action)


def manifest_row(phase: str, requirement: str, path: str, min_rows: int, next_action: str) -> AuditRow:
    rows = count_jsonl(path)
    if rows is None:
        return AuditRow(phase, requirement, "MISSING", path, "manifest missing", next_action)
    if rows < min_rows:
        return AuditRow(phase, requirement, "BLOCKED", path, f"rows={rows}, required>={min_rows}", next_action)
    return AuditRow(phase, requirement, "PASS", path, f"rows={rows}")


def json_decision_row(
    phase: str,
    requirement: str,
    path: str,
    pass_values: set[str],
    next_action: str,
) -> AuditRow:
    decision = read_json_decision(path)
    status = status_from_decision(decision, pass_values)
    return AuditRow(phase, requirement, status, path, f"decision={decision}", "" if status == "PASS" else next_action)


def md_decision_row(
    phase: str,
    requirement: str,
    path: str,
    pass_values: set[str],
    next_action: str,
) -> AuditRow:
    decision = read_md_decision(path)
    status = status_from_decision(decision, pass_values)
    return AuditRow(phase, requirement, status, path, f"decision={decision}", "" if status == "PASS" else next_action)


def git_forbidden_row() -> AuditRow:
    proc = subprocess.run(["git", "diff", "--cached", "--name-only"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if proc.returncode != 0:
        return AuditRow("safety", "forbidden staged large artifacts", "BLOCKED", "git diff --cached --name-only", proc.stdout[-1000:], "inspect git index")
    offenders = [line for line in proc.stdout.splitlines() if FORBIDDEN_RE.search(line)]
    if offenders:
        return AuditRow("safety", "forbidden staged large artifacts", "BLOCKED", "git diff --cached --name-only", ";".join(offenders), "unstage forbidden large/video/checkpoint files")
    return AuditRow("safety", "forbidden staged large artifacts", "PASS", "git diff --cached --name-only", "none")


def build_rows() -> list[AuditRow]:
    rows: list[AuditRow] = []
    rows.extend([
        file_row("phase0_prd", "PRD written before execution", "docs/experiments/EXP_physeditworld_50h_prompt_gravity_lingbotfast.md", "write PRD"),
        file_row("phase0_prd", "current status document", "docs/physeditworld_50h_current_status.md", "write status doc"),
        file_row("phase0_migration", "environment export", "reports/migration/environment_no_builds.yml", "export conda environment"),
        file_row("phase0_migration", "pip freeze export", "reports/migration/pip_freeze.txt", "export pip freeze"),
        file_row("phase0_migration", "migration audit collector wrapper", "scripts/migration/collect_physeditworld_migration_audit_bundle.sh", "add migration audit collector"),
        file_row("phase0_migration", "root submission template wrapper", "scripts/migration/write_physeditworld_root_submission_template.sh", "write external root submission template wrapper"),
        file_row("phase0_migration", "root submission validation wrapper", "scripts/migration/validate_physeditworld_root_submission.sh", "write external root submission validator wrapper"),
        file_row("phase0_migration", "required weights manifest", "reports/migration/required_weights_manifest.tsv", "build weights manifest"),
        file_row("phase0_migration", "required data manifest", "reports/migration/required_data_manifest.tsv", "build data manifest"),
        file_row("phase0_migration", "guarded dry-run rsync script", "scripts/migration/rsync_h20_to_pai_dryrun.sh", "add migration dry-run script"),
        file_row("phase0_migration", "guarded execute rsync script", "scripts/migration/rsync_h20_to_pai_execute.sh", "add guarded migration execute script"),
        file_row("phase0_migration", "explicit copy-plan template", "reports/migration/approved_copy_manifest_template.tsv", "generate approved copy manifest template"),
        file_row("phase0_migration", "external selected-root submission TSV", "reports/migration/physeditworld_root_submission_template.tsv", "run root submission template writer"),
        file_row("phase0_migration", "external selected-root submission guide", "reports/migration/physeditworld_root_submission_template.md", "run root submission template writer"),
        file_row("phase0_migration", "PAI bootstrap restore entrypoint", "scripts/migration/bootstrap_pai_physeditworld.sh", "add PAI bootstrap script"),
        file_row("phase0_migration", "PAI bootstrap operator guide", "docs/physeditworld_50h_pai_bootstrap.md", "write PAI bootstrap guide"),
        file_row("phase0_migration", "PAI restore-packet wrapper", "scripts/migration/run_physeditworld_pai_restore_packet.sh", "add restore-packet wrapper"),
        file_row("phase0_migration", "post-mount continuation wrapper", "scripts/continue_physeditworld_after_mount.sh", "add post-mount continuation wrapper"),
        file_row("phase0_migration", "post-mount continuation operator guide", "docs/physeditworld_50h_post_mount_continue.md", "write post-mount continuation guide"),
        file_row("phase0_migration", "PAI restore-packet summary", "reports/migration/pai_restore_packet.md", "run restore-packet writer"),
        file_row("phase0_migration", "external unblock-packet wrapper", "scripts/migration/write_physeditworld_external_unblock_packet.sh", "add external unblock packet wrapper"),
        file_row("phase0_migration", "external unblock-packet summary", "reports/migration/physeditworld_external_unblock_packet.md", "run external unblock packet writer"),
        json_decision_row("phase0_migration", "H20 read-only migration audit bundle", "reports/migration/migration_audit_bundle.json", {"MIGRATION_AUDIT_BUNDLE_READY"}, "run migration audit bundle collector before migration/handoff"),
        json_decision_row("phase0_migration", "PhysEditWorld GPU command policy audit", "reports/physeditworld_50h/gpu_policy/gpu_command_policy_audit.json", {"PHYS_EDITWORLD_GPU_COMMAND_POLICY_PASS"}, "run GPU command policy audit and remove any forbidden GPU0-3 assignments from PhysEditWorld runnable artifacts"),
        json_decision_row("phase0_migration", "Git tracked artifact policy audit", "reports/migration/git_artifact_policy_audit.json", {"GIT_ARTIFACT_POLICY_PASS", "GIT_ARTIFACT_POLICY_PASS_WITH_SIZE_WARNINGS"}, "remove tracked forbidden videos/images/weights/checkpoints/logs from git before handoff"),
        json_decision_row(
            "phase0_migration",
            "migration candidate and approved-payload size summary",
            "reports/migration/migration_size_summary.json",
            {
                "MIGRATION_SIZE_SUMMARY_NO_APPROVED_ROWS",
                "MIGRATION_SIZE_SUMMARY_NAS_BLOCKED",
                "MIGRATION_SIZE_SUMMARY_APPROVED_SOURCE_MISSING",
                "MIGRATION_SIZE_SUMMARY_READY_FOR_APPROVED_DRYRUN",
            },
            "run migration size summary after migration manifests are generated",
        ),
        json_decision_row(
            "phase0_migration",
            "external selected-root submission template",
            "reports/migration/physeditworld_root_submission_template.json",
            {"PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY"},
            "write the root submission template before asking external/PAI owners to provide the selected 50h root",
        ),
        json_decision_row(
            "phase0_migration",
            "external selected-root submission validation",
            "reports/migration/physeditworld_root_submission_validation.json",
            {"PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_READY_FOR_SCHEMA_PROBE", "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE"},
            "fill and validate the selected-root submission before schema probe",
        ),
        json_decision_row(
            "phase0_migration",
            "migration approval review packet",
            "reports/migration/migration_approval_review_packet.json",
            {"MIGRATION_APPROVAL_REVIEW_PACKET_READY"},
            "rank the approved-copy template rows for explicit review before any approval or copy",
        ),
        json_decision_row("phase0_migration", "expected empty manifest placeholders", "reports/physeditworld_50h/manifest_init/empty_manifest_init.json", {"PHYS_EDITWORLD_EMPTY_MANIFESTS_INITIALIZED", "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT"}, "run scripts/migration/init_physeditworld_empty_manifests.sh"),
        json_decision_row("phase0_migration", "locked handoff sequence", "reports/migration/locked_handoff_sequence.json", {"LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE"}, "set PHYS_EDITWORLD_ROOTS to a strong root and rerun locked handoff sequence"),
        json_decision_row("phase0_migration", "selected-root schema probe", "reports/migration/physeditworld_root_schema_probe.json", {"PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"}, "provide selected root and rerun schema probe"),
        json_decision_row("phase0_migration", "selected-root intake handoff report", "reports/migration/physeditworld_root_intake.json", {"PHYS_EDITWORLD_ROOT_INTAKE_LOCKED_READY_FOR_HANDOFF"}, "provide selected root and rerun root intake/handoff"),
        json_decision_row("phase0_migration", "selected-root lock", "reports/migration/physeditworld_selected_root_status.json", {"PHYS_EDITWORLD_ROOT_SELECTION_LOCKED"}, "provide selected PhysEditWorld 50h root and rerun root selector"),
        json_decision_row("phase0_migration", "PAI handoff verifier", "reports/migration/pai_handoff_status.json", {"PAI_HANDOFF_READY_FOR_POST_MOUNT_CONTINUE"}, "mount NAS/root and rerun PAI handoff"),
        json_decision_row("phase0_migration", "migration asset validation", "reports/migration/migration_asset_validation.json", {"MIGRATION_ASSET_VALIDATION_PASS"}, "mount NAS and validate required assets"),
        json_decision_row("phase0_migration", "approved-only migration copy", "reports/migration/approved_copy_status.json", {"APPROVED_COPY_DRYRUN_READY", "APPROVED_COPY_EXECUTED"}, "approve required rows after review and rerun dry-run"),
        json_decision_row("phase0_migration", "PAI restore packet decision", "reports/migration/pai_restore_packet.json", {"PAI_RESTORE_PACKET_READY_FOR_POST_MOUNT"}, "mount NAS, set PHYS_EDITWORLD_ROOTS, rerun bootstrap or restore-packet writer"),
        json_decision_row("phase0_migration", "external unblock packet decision", "reports/migration/physeditworld_external_unblock_packet.json", {"PHYS_EDITWORLD_EXTERNAL_UNBLOCK_PACKET_READY_FOR_POST_MOUNT"}, "mount NAS, set PHYS_EDITWORLD_ROOTS, rerun external unblock packet writer and bootstrap"),
        json_decision_row("phase0_migration", "post-mount Phase1/2 continuation gate", "reports/physeditworld_50h/post_mount/post_mount_status.json", {"POST_MOUNT_PHASE12_DONE_RUN_PIPELINE_GATE_NEXT"}, "set PHYS_EDITWORLD_ROOTS, select/lock the root, and rerun post-mount continuation"),
        manifest_row("phase1_data", "strict PhysEditWorld 50h manifest", "manifests/physeditworld_50h_all.jsonl", 1, "mount selected root and run manifest audit"),
        manifest_row("phase1_data", "train split no replay leakage", "manifests/physeditworld_50h_train.jsonl", 1, "run replay-group split after data audit"),
        file_row("phase1_data", "split summary", "reports/physeditworld_50h/split_summary.md", "write split summary"),
        file_row("phase1_data", "replay-group leakage check", "reports/physeditworld_50h/replay_group_leakage_check.csv", "run replay leakage check"),
        json_decision_row("phase2_conversion", "prompt-only gravity policy audit", "reports/physeditworld_50h/prompt_gravity_policy/prompt_gravity_policy_audit.json", {"PHYS_EDITWORLD_PROMPT_GRAVITY_POLICY_PASS"}, "fix prompt-only gravity policy before conversion or warm-up"),
        manifest_row("phase2_conversion", "LingBot train conversion manifest", "manifests/physeditworld_50h_lingbot_train.jsonl", 1, "run prompt-only gravity conversion"),
        manifest_row("phase2_conversion", "LingBot val conversion manifest", "manifests/physeditworld_50h_lingbot_val.jsonl", 1, "run prompt-only gravity conversion"),
        json_decision_row(
            "phase2_conversion",
            "LingBot train conversion schema validation",
            "reports/physeditworld_50h/conversion_validation/lingbot_train_manifest_validation.json",
            {"LINGBOT_MANIFEST_SCHEMA_PASS"},
            "rerun conversion manifest validator after prompt-only LingBot conversion writes rows",
        ),
        json_decision_row(
            "phase2_conversion",
            "LingBot val conversion schema validation",
            "reports/physeditworld_50h/conversion_validation/lingbot_val_manifest_validation.json",
            {"LINGBOT_MANIFEST_SCHEMA_PASS"},
            "rerun conversion manifest validator after prompt-only LingBot conversion writes rows",
        ),
        json_decision_row(
            "phase3_baseline",
            "LingBot backend readiness for baseline/warm-up/checkpoint eval",
            "reports/physeditworld_50h/backend_readiness/backend_readiness.json",
            {"PHYS_EDITWORLD_BACKEND_READY_FOR_BASELINE_WARMUP"},
            "connect real LingBot-Fast baseline rollout, checkpoint eval, and rank32 warm-up backend before Phase3/4/5",
        ),
        md_decision_row("phase3_baseline", "baseline true rollout gate", "reports/physeditworld_50h_baseline_rollout/summary.md", {"BASELINE_ROLLOUT_PASS", "PROMPT_ONLY_GRAVITY_BASELINE_WEAK"}, "run baseline rollout after LingBot manifests exist"),
        md_decision_row("phase4_warmup", "rank32 warm-up preflight", "reports/physeditworld_50h_warmup_rank32/preflight_summary.md", {"WARMUP_PREFLIGHT_PASS"}, "run 5-step warm-up preflight after conversion"),
        json_decision_row("phase5_checkpoint_eval", "warm-up checkpoint video/metric gate", "reports/physeditworld_50h_warmup_rank32/best_checkpoint_decision.json", {"WARMUP_GATE_PASS"}, "run checkpoint rollout, metrics, and Codex visual audit"),
        manifest_row("phase6_pairs", "anchored DPO pair manifest", "manifests/physeditworld_dpo_pairs_anchored_v0.jsonl", 100, "build >=100 reviewed anchored pairs after warm-up gate"),
        json_decision_row(
            "phase6_pairs",
            "strict anchored pair manifest validation",
            "reports/physeditworld_dpo_pairs_anchored_v0/pair_manifest_validation.json",
            {"PHYS_EDITWORLD_PAIR_MANIFEST_PASS"},
            "run pair manifest validator and ensure every pair has visual audit, reward/gravity margin, and matched condition/action/camera/intrinsics/gravity",
        ),
        json_decision_row("phase7_tiny_dpo", "tiny anchored DPO gate", "reports/physeditworld_tiny_dpo_v0/best_checkpoint_decision.json", {"TINY_DPO_PASS"}, "run tiny anchored DPO only after pair gate"),
        file_row("phase8_ablation", "PhysEditWorld50 plus OurPhysics50 ablation plan", "docs/experiments/EXP_physeditworld50_plus_ourphysics50_ablation_plan.md", "write future ablation plan"),
        git_forbidden_row(),
    ])
    return rows


PHASE_ORDER = [
    "phase0_prd",
    "phase0_migration",
    "phase1_data",
    "phase2_conversion",
    "phase3_baseline",
    "phase4_warmup",
    "phase5_checkpoint_eval",
    "phase6_pairs",
    "phase7_tiny_dpo",
    "phase8_ablation",
    "safety",
]


def overall_decision(rows: list[AuditRow]) -> str:
    if any(row.phase == "safety" and row.status == "BLOCKED" for row in rows):
        return "PHYS_EDITWORLD_OBJECTIVE_BLOCKED_AT_SAFETY"
    for phase in PHASE_ORDER:
        phase_rows = [row for row in rows if row.phase == phase]
        if any(row.status in {"BLOCKED", "MISSING", "UNKNOWN"} for row in phase_rows):
            return "PHYS_EDITWORLD_OBJECTIVE_INCOMPLETE_AT_" + phase.upper()
    return "PHYS_EDITWORLD_OBJECTIVE_COMPLETE"


def write_csv(rows: list[AuditRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(AuditRow.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[AuditRow], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "rows": [asdict(row) for row in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[AuditRow], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    lines = ["# PhysEditWorld 50h Objective Completion Audit", "", f"Decision: `{decision}`", "", "## Status Counts", ""]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    lines.extend(["", "## Requirement Evidence", ""])
    for row in rows:
        lines.append(f"- `{row.phase}` / {row.requirement}: `{row.status}`")
        lines.append(f"  - evidence: `{row.evidence}`")
        if row.detail:
            lines.append(f"  - detail: {row.detail}")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    lines.extend([
        "",
        "## Safety",
        "",
        "This audit is CPU/IO only. It does not copy files, delete files, use GPUs, train, rollout, run DPO, or push large artifacts.",
        "A PASS here requires evidence for the original PhysEditWorld migration, data, conversion, baseline, warm-up, checkpoint-eval, pair, and tiny-DPO gates.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Audit completion of the full PhysEditWorld 50h objective")
    ap.add_argument("--output_csv", default="reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.csv")
    ap.add_argument("--output_json", default="reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json")
    ap.add_argument("--summary", default="reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = build_rows()
    decision = overall_decision(rows)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json)
    write_summary(rows, decision, args.summary)
    print(json.dumps({"decision": decision, "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
