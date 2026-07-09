from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

FORBIDDEN_STAGED_RE = re.compile(
    r"(^local_assets/|\.(mp4|jpg|jpeg|png|hdf5|h5|npy|npz|pt|pth|safetensors|ckpt|bin|tar|zip|log)$)",
    re.IGNORECASE,
)

REQUIRED_FILES = (
    "docs/physeditworld_50h_current_status.md",
    "docs/experiments/EXP_physeditworld_50h_prompt_gravity_lingbotfast.md",
    "docs/physeditworld_50h_pai_bootstrap.md",
    "scripts/migration/bootstrap_pai_physeditworld.sh",
    "scripts/migration/check_physeditworld_pai_readiness.sh",
    "scripts/migration/run_physeditworld_pai_restore_packet.sh",
    "scripts/migration/write_physeditworld_external_unblock_packet.sh",
    "scripts/migration/init_physeditworld_empty_manifests.sh",
    "scripts/migration/rank_physeditworld_root_candidates.sh",
    "scripts/migration/write_physeditworld_root_submission_template.sh",
    "scripts/migration/probe_physeditworld_root_schema.sh",
    "scripts/migration/select_physeditworld_root.sh",
    "scripts/migration/validate_physeditworld_migration_assets.sh",
    "scripts/migration/build_physeditworld_migration_copy_plan.sh",
    "scripts/migration/run_approved_migration_copy.sh",
    "scripts/migration/run_physeditworld_phase0_preflight.sh",
    "scripts/migration/run_physeditworld_locked_handoff_sequence.sh",
    "scripts/migration/run_physeditworld_completion_audit.sh",
    "scripts/migration/prepare_physeditworld_root_intake.sh",
    "scripts/migration/verify_pai_physeditworld_handoff.sh",
    "scripts/continue_physeditworld_after_mount.sh",
    "scripts/run_physeditworld_pipeline_gates.sh",
    "cam_physgeo/data/physeditworld_readiness.py",
    "cam_physgeo/data/physeditworld_manifest_init.py",
    "cam_physgeo/data/physeditworld_root_candidates.py",
    "cam_physgeo/data/physeditworld_root_schema_probe.py",
    "cam_physgeo/data/physeditworld_root_selection.py",
    "cam_physgeo/orchestration/physeditworld_phase0_preflight.py",
    "cam_physgeo/orchestration/physeditworld_pipeline_gate.py",
    "cam_physgeo/orchestration/physeditworld_backend_readiness.py",
    "cam_physgeo/orchestration/physeditworld_requirement_matrix.py",
    "cam_physgeo/orchestration/physeditworld_locked_handoff.py",
    "cam_physgeo/orchestration/physeditworld_completion_audit.py",
    "cam_physgeo/orchestration/physeditworld_pai_restore_packet.py",
    "cam_physgeo/orchestration/physeditworld_external_unblock_packet.py",
    "cam_physgeo/orchestration/physeditworld_root_intake.py",
    "cam_physgeo/orchestration/physeditworld_root_submission_template.py",
    "cam_physgeo/orchestration/physeditworld_pai_handoff.py",
    "cam_physgeo/orchestration/migration_size_summary.py",
    "cam_physgeo/orchestration/migration_approval_review_packet.py",
)

EXPECTED_REPORTS = (
    "reports/migration/phase0_preflight_status.json",
    "reports/migration/phase0_preflight_summary.md",
    "reports/physeditworld_50h/manifest_init/empty_manifest_init.json",
    "reports/migration/physeditworld_pai_readiness.json",
    "reports/migration/physeditworld_root_candidates_ranked.json",
    "reports/migration/physeditworld_root_submission_template.json",
    "reports/migration/physeditworld_root_schema_probe.json",
    "reports/migration/physeditworld_root_intake.json",
    "reports/migration/physeditworld_selected_root_status.json",
    "reports/migration/locked_handoff_sequence.json",
    "reports/migration/migration_asset_validation.json",
    "reports/migration/approved_copy_manifest_template.tsv",
    "reports/migration/approved_copy_status.json",
    "reports/migration/migration_size_summary.json",
    "reports/migration/migration_approval_review_packet.json",
    "reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json",
    "reports/physeditworld_50h/backend_readiness/backend_readiness.json",
    "reports/physeditworld_50h/requirement_matrix.json",
    "reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json",
    "reports/migration/pai_restore_packet.json",
    "reports/migration/physeditworld_external_unblock_packet.json",
)


@dataclass
class HandoffCheck:
    name: str
    status: str
    path: str = ""
    detail: str = ""
    next_action: str = ""
    error_reason: str = ""


def run_text(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return proc.returncode, proc.stdout.strip()


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
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        return str(obj.get("decision") or obj.get("status") or "UNKNOWN")
    except Exception as exc:
        return "UNREADABLE:" + repr(exc)


def check_git(expected_branch: str) -> list[HandoffCheck]:
    rows: list[HandoffCheck] = []
    code, branch = run_text(["git", "branch", "--show-current"])
    if code != 0:
        rows.append(HandoffCheck("git_branch", "BLOCKED", detail="git branch command failed", error_reason=branch))
    elif branch == expected_branch:
        rows.append(HandoffCheck("git_branch", "PASS", detail=f"branch={branch}"))
    else:
        rows.append(HandoffCheck("git_branch", "BLOCKED", detail=f"branch={branch}", next_action=f"checkout {expected_branch}"))
    code, head = run_text(["git", "rev-parse", "--short", "HEAD"])
    rows.append(HandoffCheck("git_head", "PASS" if code == 0 else "BLOCKED", detail=head, error_reason="" if code == 0 else head))
    code, staged = run_text(["git", "diff", "--cached", "--name-only"])
    if code != 0:
        rows.append(HandoffCheck("forbidden_staged_files", "BLOCKED", error_reason=staged))
    else:
        offenders = [line for line in staged.splitlines() if FORBIDDEN_STAGED_RE.search(line)]
        rows.append(HandoffCheck(
            "forbidden_staged_files",
            "BLOCKED" if offenders else "PASS",
            detail=";".join(offenders) if offenders else "none",
            next_action="unstage forbidden large/video/checkpoint files" if offenders else "",
        ))
    return rows


def check_required_files(paths: tuple[str, ...]) -> HandoffCheck:
    missing = [p for p in paths if not Path(p).exists()]
    return HandoffCheck(
        "required_handoff_files",
        "BLOCKED" if missing else "PASS",
        detail=f"missing={len(missing)} total={len(paths)}",
        error_reason=";".join(missing[:20]),
        next_action="restore/push missing handoff code and docs" if missing else "",
    )


def check_reports(paths: tuple[str, ...]) -> HandoffCheck:
    missing = [p for p in paths if not Path(p).exists()]
    decisions = {p: read_decision(p) for p in paths if p.endswith(".json") and Path(p).exists()}
    detail = f"missing={len(missing)} total={len(paths)} decisions=" + json.dumps(decisions, sort_keys=True)
    return HandoffCheck(
        "phase0_report_artifacts",
        "BLOCKED" if missing else "PASS",
        detail=detail,
        error_reason=";".join(missing[:20]),
        next_action="run bash scripts/migration/run_physeditworld_phase0_preflight.sh" if missing else "",
    )


def check_nas(path: str) -> HandoffCheck:
    p = Path(path)
    if not p.exists():
        return HandoffCheck("nas_target", "BLOCKED", str(p), "missing", "mount or expose PAI/NAS target path")
    if not p.is_dir():
        return HandoffCheck("nas_target", "BLOCKED", str(p), "not a directory", "fix NAS target path")
    readable = os.access(p, os.R_OK)
    writable = os.access(p, os.W_OK)
    if readable and writable:
        return HandoffCheck("nas_target", "PASS", str(p), "readable,writable")
    return HandoffCheck("nas_target", "BLOCKED", str(p), f"readable={readable} writable={writable}", "fix NAS permissions or choose writable target")


def split_roots(raw: str) -> list[str]:
    if not raw.strip():
        return []
    out: list[str] = []
    for chunk in raw.replace(",", os.pathsep).split(os.pathsep):
        if chunk.strip():
            out.append(chunk.strip())
    return out


def check_root_input(raw_roots: str) -> HandoffCheck:
    roots = split_roots(raw_roots)
    if not roots:
        return HandoffCheck("physeditworld_root_input", "BLOCKED", detail="PHYS_EDITWORLD_ROOTS not set", next_action="set PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h")
    existing = [r for r in roots if Path(r).exists()]
    if existing:
        return HandoffCheck("physeditworld_root_input", "PASS", detail=";".join(existing))
    return HandoffCheck("physeditworld_root_input", "BLOCKED", detail=";".join(roots), error_reason="no listed root exists", next_action="mount/provide the selected PhysEditWorld 50h root")


def check_manifest(path: str, name: str, min_rows: int) -> HandoffCheck:
    rows = count_jsonl(path)
    if rows is None:
        return HandoffCheck(name, "BLOCKED", path, "missing", "run post-mount manifest/conversion pipeline")
    if rows < min_rows:
        return HandoffCheck(name, "BLOCKED", path, f"rows={rows} required>={min_rows}", "mount selected root and rerun post-mount continuation")
    return HandoffCheck(name, "PASS", path, f"rows={rows}")


def build_checks(args: argparse.Namespace) -> list[HandoffCheck]:
    rows: list[HandoffCheck] = []
    rows.extend(check_git(args.expected_branch))
    rows.append(check_required_files(REQUIRED_FILES))
    rows.append(check_reports(EXPECTED_REPORTS))
    rows.append(check_nas(args.nas_path))
    rows.append(check_root_input(args.physeditworld_roots or os.environ.get("PHYS_EDITWORLD_ROOTS", "")))
    rows.append(check_manifest(args.strict_manifest, "strict_manifest", 1))
    rows.append(check_manifest(args.lingbot_train_manifest, "lingbot_train_manifest", 1))
    return rows


def overall_decision(rows: list[HandoffCheck]) -> str:
    by_name = {row.name: row for row in rows}
    if by_name.get("git_branch", HandoffCheck("", "BLOCKED")).status != "PASS" or by_name.get("required_handoff_files", HandoffCheck("", "BLOCKED")).status != "PASS":
        return "PAI_HANDOFF_BLOCKED_CODE_INCOMPLETE"
    if by_name.get("forbidden_staged_files", HandoffCheck("", "BLOCKED")).status != "PASS":
        return "PAI_HANDOFF_BLOCKED_FORBIDDEN_STAGED_FILES"
    if by_name.get("phase0_report_artifacts", HandoffCheck("", "BLOCKED")).status != "PASS":
        return "PAI_HANDOFF_BLOCKED_PHASE0_REPORTS_MISSING"
    if by_name.get("nas_target", HandoffCheck("", "BLOCKED")).status != "PASS" or by_name.get("physeditworld_root_input", HandoffCheck("", "BLOCKED")).status != "PASS":
        return "PAI_HANDOFF_BLOCKED_NAS_OR_ROOT"
    if by_name.get("strict_manifest", HandoffCheck("", "BLOCKED")).status != "PASS" or by_name.get("lingbot_train_manifest", HandoffCheck("", "BLOCKED")).status != "PASS":
        return "PAI_HANDOFF_BLOCKED_DATA_MANIFEST"
    if any(row.status == "BLOCKED" for row in rows):
        return "PAI_HANDOFF_BLOCKED_UNKNOWN"
    return "PAI_HANDOFF_READY_FOR_POST_MOUNT_CONTINUE"


def write_csv(rows: list[HandoffCheck], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(HandoffCheck.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[HandoffCheck], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "checks": [asdict(row) for row in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[HandoffCheck], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    lines = ["# PhysEditWorld PAI Handoff Verification", "", f"Decision: `{decision}`", "", "## Status Counts", ""]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    lines.extend(["", "## Checks", ""])
    for row in rows:
        loc = f" ({row.path})" if row.path else ""
        lines.append(f"- `{row.name}`: `{row.status}`{loc}")
        if row.detail:
            lines.append(f"  - detail: {row.detail}")
        if row.error_reason:
            lines.append(f"  - blocker: {row.error_reason}")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    lines.extend([
        "",
        "## Safe Next Commands",
        "",
        "```bash",
        "# Preferred one-command path after NAS/root are visible:",
        "PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h \\",
        "  bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh",
        "",
        "# Read-only completion evidence after any handoff run:",
        "python3 -m cam_physgeo.orchestration.physeditworld_backend_readiness",
        "bash scripts/migration/run_physeditworld_completion_audit.sh",
        "bash scripts/migration/run_physeditworld_pai_restore_packet.sh",
        "",
        "# Lower-level fallback commands for debugging one stage at a time:",
        "PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h bash scripts/migration/select_physeditworld_root.sh",
        "PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h bash scripts/continue_physeditworld_after_mount.sh",
        "bash scripts/migration/run_physeditworld_phase0_preflight.sh",
        "bash scripts/run_physeditworld_pipeline_gates.sh",
        "```",
        "",
        "## Safety",
        "",
        "This verifier is CPU/IO only. It does not copy files, run rsync execute, train, rollout, evaluate videos, use GPUs, delete data, or push local_assets/checkpoints/videos.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Verify PAI handoff readiness for PhysEditWorld 50h pipeline")
    ap.add_argument("--expected_branch", default="physion-only-local-assets-videogpa-smoke")
    ap.add_argument("--nas_path", default="/mnt/workspace/hj/nas_hj")
    ap.add_argument("--physeditworld_roots", default="")
    ap.add_argument("--strict_manifest", default="manifests/physeditworld_50h_all.jsonl")
    ap.add_argument("--lingbot_train_manifest", default="manifests/physeditworld_50h_lingbot_train.jsonl")
    ap.add_argument("--output_csv", default="reports/migration/pai_handoff_status.csv")
    ap.add_argument("--output_json", default="reports/migration/pai_handoff_status.json")
    ap.add_argument("--summary", default="reports/migration/pai_handoff_summary.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = build_checks(args)
    decision = overall_decision(rows)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json)
    write_summary(rows, decision, args.summary)
    print(json.dumps({"decision": decision, "checks": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
