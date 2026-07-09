from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


READY_BACKEND = "PHYS_EDITWORLD_BACKEND_READY_FOR_BASELINE_WARMUP"
READY_MATRIX = "PHYS_EDIT_WORLD_PIPELINE_REQUIREMENTS_PASS"
READY_COMPLETION = "PHYS_EDITWORLD_OBJECTIVE_COMPLETE"


DECISION_REPORTS: tuple[tuple[str, str], ...] = (
    ("pai_handoff", "reports/migration/pai_handoff_status.json"),
    ("phase0_preflight", "reports/migration/phase0_preflight_status.json"),
    ("root_candidates", "reports/migration/physeditworld_root_candidates_ranked.json"),
    ("root_submission_template", "reports/migration/physeditworld_root_submission_template.json"),
    ("root_submission_validation", "reports/migration/physeditworld_root_submission_validation.json"),
    ("root_evidence_samples", "reports/migration/physeditworld_root_evidence_samples.json"),
    ("root_schema_probe", "reports/migration/physeditworld_root_schema_probe.json"),
    ("root_selection", "reports/migration/physeditworld_selected_root_status.json"),
    ("root_intake", "reports/migration/physeditworld_root_intake.json"),
    ("locked_handoff", "reports/migration/locked_handoff_sequence.json"),
    ("migration_asset_validation", "reports/migration/migration_asset_validation.json"),
    ("approved_copy", "reports/migration/approved_copy_status.json"),
    ("migration_size_summary", "reports/migration/migration_size_summary.json"),
    ("migration_approval_review", "reports/migration/migration_approval_review_packet.json"),
    ("backend_readiness", "reports/physeditworld_50h/backend_readiness/backend_readiness.json"),
    ("pipeline_gate", "reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json"),
    ("requirement_matrix", "reports/physeditworld_50h/requirement_matrix.json"),
    ("completion_audit", "reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json"),
)


MANIFESTS: tuple[str, ...] = (
    "manifests/physeditworld_50h_all.jsonl",
    "manifests/physeditworld_50h_train.jsonl",
    "manifests/physeditworld_50h_val.jsonl",
    "manifests/physeditworld_50h_test.jsonl",
    "manifests/physeditworld_50h_lingbot_train.jsonl",
    "manifests/physeditworld_50h_lingbot_val.jsonl",
    "manifests/physeditworld_dpo_pairs_anchored_v0.jsonl",
)


RESTORE_ENTRYPOINTS: tuple[str, ...] = (
    "scripts/migration/bootstrap_pai_physeditworld.sh",
    "scripts/migration/run_physeditworld_pai_restore_packet.sh",
    "docs/physeditworld_50h_pai_bootstrap.md",
)


SAFE_NEXT_COMMANDS: tuple[str, ...] = (
    "export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root",
    "bash scripts/migration/write_physeditworld_root_submission_template.sh",
    "bash scripts/migration/validate_physeditworld_root_submission.sh",
    "bash scripts/migration/sample_physeditworld_root_evidence.sh",
    "bash scripts/migration/bootstrap_pai_physeditworld.sh",
    "bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh",
    "bash scripts/migration/write_physeditworld_external_unblock_packet.sh",
    "bash scripts/migration/verify_pai_physeditworld_handoff.sh",
    "bash scripts/migration/run_physeditworld_phase0_preflight.sh",
    "python3 -m cam_physgeo.orchestration.physeditworld_backend_readiness",
    "bash scripts/run_physeditworld_pipeline_gates.sh",
    "python3 -m cam_physgeo.orchestration.physeditworld_requirement_matrix",
    "bash scripts/migration/run_physeditworld_completion_audit.sh",
    "bash scripts/migration/run_physeditworld_pai_restore_packet.sh",
)


@dataclass
class PathCheck:
    path: str
    exists: bool
    is_dir: bool = False
    detail: str = ""


@dataclass
class DecisionCheck:
    name: str
    path: str
    exists: bool
    decision: str
    error_reason: str = ""


@dataclass
class ManifestCheck:
    path: str
    exists: bool
    rows: int | None
    status: str


def run_text(cmd: list[str], timeout_seconds: int = 10) -> str:
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout_seconds,
        )
    except Exception as exc:  # pragma: no cover - defensive around host tools
        return "ERROR:" + repr(exc)
    return proc.stdout.strip()


def read_json(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"__error__": repr(exc)}


def read_decision(path: str | Path) -> tuple[str, str]:
    obj = read_json(path)
    if obj is None:
        return "MISSING", ""
    if "__error__" in obj:
        return "UNREADABLE", str(obj["__error__"])
    return str(obj.get("decision") or obj.get("status") or "UNKNOWN"), ""


def count_jsonl(path: str | Path) -> int | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def split_roots(raw: str) -> list[str]:
    roots: list[str] = []
    for chunk in raw.replace(",", ":").split(":"):
        item = chunk.strip()
        if item:
            roots.append(item)
    return roots


def check_path(path: str) -> PathCheck:
    p = Path(path)
    if p.exists():
        return PathCheck(path=path, exists=True, is_dir=p.is_dir(), detail="exists")
    return PathCheck(path=path, exists=False, is_dir=False, detail="missing")


def collect_git() -> dict[str, str]:
    branch = run_text(["git", "branch", "--show-current"])
    head = run_text(["git", "rev-parse", "--short", "HEAD"])
    remote_head = run_text(["git", "rev-parse", "--short", f"origin/{branch}"]) if branch and not branch.startswith("ERROR") else "UNKNOWN"
    remote = run_text(["git", "remote", "-v"])
    status = run_text(["git", "status", "--short"])
    return {
        "branch": branch,
        "head": head,
        "origin_branch_head": remote_head,
        "remote": remote,
        "status_short_first_80": "\n".join(status.splitlines()[:80]),
    }


def collect_decisions() -> list[DecisionCheck]:
    rows: list[DecisionCheck] = []
    for name, path in DECISION_REPORTS:
        p = Path(path)
        decision, error = read_decision(p)
        rows.append(DecisionCheck(name=name, path=path, exists=p.exists(), decision=decision, error_reason=error))
    return rows


def collect_manifests() -> list[ManifestCheck]:
    rows: list[ManifestCheck] = []
    for path in MANIFESTS:
        rows_count = count_jsonl(path)
        if rows_count is None:
            rows.append(ManifestCheck(path=path, exists=False, rows=None, status="MISSING"))
        elif rows_count == 0:
            rows.append(ManifestCheck(path=path, exists=True, rows=0, status="EMPTY"))
        else:
            rows.append(ManifestCheck(path=path, exists=True, rows=rows_count, status="NONEMPTY"))
    return rows


def decide_restore_packet(nas_visible: bool, valid_root_count: int, decisions: dict[str, str]) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if not nas_visible:
        blockers.append("NAS_TARGET_MISSING")
    if valid_root_count < 1:
        blockers.append("PHYS_EDITWORLD_ROOTS_MISSING_OR_INVALID")
    backend = decisions.get("backend_readiness", "MISSING")
    if backend != READY_BACKEND:
        blockers.append("BACKEND_NOT_READY:" + backend)
    matrix = decisions.get("requirement_matrix", "MISSING")
    if matrix != READY_MATRIX:
        blockers.append("REQUIREMENT_MATRIX_NOT_PASS:" + matrix)
    completion = decisions.get("completion_audit", "MISSING")
    if completion != READY_COMPLETION:
        blockers.append("OBJECTIVE_NOT_COMPLETE:" + completion)
    if not nas_visible or valid_root_count < 1:
        return "PAI_RESTORE_PACKET_BLOCKED_NAS_OR_ROOT", blockers
    if backend != READY_BACKEND:
        return "PAI_RESTORE_PACKET_BLOCKED_BACKEND_READINESS", blockers
    if blockers:
        return "PAI_RESTORE_PACKET_READY_WITH_BLOCKERS", blockers
    return "PAI_RESTORE_PACKET_READY_FOR_POST_MOUNT", blockers


def build_packet(nas_root: str) -> dict[str, Any]:
    nas_check = check_path(nas_root)
    root_env = os.environ.get("PHYS_EDITWORLD_ROOTS", "")
    root_checks = [check_path(root) for root in split_roots(root_env)]
    valid_root_count = sum(1 for row in root_checks if row.exists)
    decisions = collect_decisions()
    decision_map = {row.name: row.decision for row in decisions}
    decision, blockers = decide_restore_packet(nas_check.exists, valid_root_count, decision_map)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "blockers": blockers,
        "repo": str(Path.cwd()),
        "git": collect_git(),
        "nas_target": asdict(nas_check),
        "physeditworld_roots_env": root_env,
        "physeditworld_roots": [asdict(row) for row in root_checks],
        "restore_entrypoints": [asdict(check_path(path)) for path in RESTORE_ENTRYPOINTS],
        "decisions": [asdict(row) for row in decisions],
        "migration_size_summary": read_json("reports/migration/migration_size_summary.json") or {},
        "manifests": [asdict(row) for row in collect_manifests()],
        "disk": run_text(["df", "-h", "/home/nvme03", "/home/nvme04", nas_root], timeout_seconds=10),
        "safe_next_commands": list(SAFE_NEXT_COMMANDS),
        "safety": {
            "gpu_policy": "No GPU work is performed by this restore packet. Future GPU work must use only physical GPU4-7.",
            "non_runs": [
                "no training",
                "no rollout",
                "no DPO",
                "no deletion",
                "no rsync execute",
                "no local_assets/video/checkpoint/weight push",
            ],
        },
    }


def write_json(packet: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(packet: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PhysEditWorld PAI Restore Packet",
        "",
        f"Generated UTC: `{packet['generated_at_utc']}`",
        f"Decision: `{packet['decision']}`",
        "",
        "## Git",
        "",
        f"- repo: `{packet['repo']}`",
        f"- branch: `{packet['git']['branch']}`",
        f"- local head: `{packet['git']['head']}`",
        f"- origin branch head: `{packet['git']['origin_branch_head']}`",
        "",
        "## Current Blockers",
        "",
    ]
    if packet["blockers"]:
        for blocker in packet["blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## NAS And Root",
        "",
        f"- NAS target `{packet['nas_target']['path']}`: `{packet['nas_target']['detail']}`",
        f"- `PHYS_EDITWORLD_ROOTS`: `{packet['physeditworld_roots_env'] or 'UNSET'}`",
    ])
    for root in packet["physeditworld_roots"]:
        lines.append(f"- root `{root['path']}`: `{root['detail']}`")
    if not packet["physeditworld_roots"]:
        lines.append("- no root candidates supplied via `PHYS_EDITWORLD_ROOTS`")
    lines.extend(["", "## Decisions", ""])
    for row in packet["decisions"]:
        lines.append(f"- `{row['name']}`: `{row['decision']}` (`{row['path']}`)")
    size_summary = packet.get("migration_size_summary") or {}
    candidate = size_summary.get("candidate_summary", {}) if isinstance(size_summary, dict) else {}
    approved = size_summary.get("approved_copy_summary", {}) if isinstance(size_summary, dict) else {}
    approved_status = size_summary.get("approved_copy_status", {}) if isinstance(size_summary, dict) else {}
    lines.extend(["", "## Migration Size Snapshot", ""])
    if size_summary:
        lines.append(f"- decision: `{size_summary.get('decision', 'UNKNOWN')}`")
        lines.append(f"- candidate rows: `{candidate.get('manifest_rows', 'unknown')}`")
        lines.append(f"- candidate present file bytes: `{candidate.get('present_file_bytes', 'unknown')}` ({candidate.get('present_file_bytes_human', 'unknown')})")
        lines.append(f"- directory rows pending recursive sizing: `{candidate.get('dir_rows_pending_recursive_size', 'unknown')}`")
        lines.append(f"- candidate missing rows: `{candidate.get('missing_rows', 'unknown')}`")
        lines.append(f"- approved-copy decision: `{approved_status.get('decision', 'UNKNOWN')}`")
        lines.append(f"- approved rows: `{approved.get('approved_rows', 'unknown')}`")
        lines.append(f"- approved present file bytes: `{approved.get('approved_present_file_bytes', 'unknown')}`")
    else:
        lines.append("- migration size summary missing")
    lines.extend(["", "## Manifest Rows", ""])
    for row in packet["manifests"]:
        lines.append(f"- `{row['path']}`: `{row['status']}` rows={row['rows']}")
    lines.extend(["", "## Restore Entrypoints", ""])
    for row in packet["restore_entrypoints"]:
        lines.append(f"- `{row['path']}`: `{row['detail']}`")
    lines.extend(["", "## Safe Next Commands", ""])
    for command in packet["safe_next_commands"]:
        lines.append(f"```bash\n{command}\n```")
    lines.extend([
        "",
        "## Safety",
        "",
        "This packet is CPU/IO only. It does not copy files, delete files, use GPUs, train, rollout, run DPO, or push large artifacts.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Write a compact PhysEditWorld H20 -> PAI restore packet")
    ap.add_argument("--nas_root", default="/mnt/workspace/hj/nas_hj")
    ap.add_argument("--output_json", default="reports/migration/pai_restore_packet.json")
    ap.add_argument("--summary", default="reports/migration/pai_restore_packet.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    packet = build_packet(args.nas_root)
    write_json(packet, args.output_json)
    write_markdown(packet, args.summary)
    print(json.dumps({"decision": packet["decision"], "blockers": packet["blockers"]}, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
