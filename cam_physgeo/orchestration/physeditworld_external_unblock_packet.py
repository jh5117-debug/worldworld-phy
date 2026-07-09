from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


NAS_TARGET_DEFAULT = "/mnt/workspace/hj/nas_hj"
REQUIRED_ROOT_EVIDENCE = (
    "video_or_frames",
    "action_trace",
    "camera_trajectory_or_poses",
    "intrinsics",
    "gravity_label_or_metadata",
    "replay_group_or_matched_replay_metadata",
)
DECISION_PATHS = (
    ("root_candidates", "reports/migration/physeditworld_root_candidates_ranked.json"),
    ("root_submission_template", "reports/migration/physeditworld_root_submission_template.json"),
    ("root_submission_validation", "reports/migration/physeditworld_root_submission_validation.json"),
    ("root_evidence_samples", "reports/migration/physeditworld_root_evidence_samples.json"),
    ("root_onboarding_sequence", "reports/migration/physeditworld_root_onboarding_sequence.json"),
    ("external_root_handoff_packet", "reports/migration/physeditworld_external_root_handoff_packet.json"),
    ("root_schema_probe", "reports/migration/physeditworld_root_schema_probe.json"),
    ("root_selection", "reports/migration/physeditworld_selected_root_status.json"),
    ("root_intake", "reports/migration/physeditworld_root_intake.json"),
    ("phase0_preflight", "reports/migration/phase0_preflight_status.json"),
    ("pai_handoff", "reports/migration/pai_handoff_status.json"),
    ("pai_restore_packet", "reports/migration/pai_restore_packet.json"),
    ("migration_size_summary", "reports/migration/migration_size_summary.json"),
    ("migration_approval_review", "reports/migration/migration_approval_review_packet.json"),
    ("backend_readiness", "reports/physeditworld_50h/backend_readiness/backend_readiness.json"),
    ("requirement_matrix", "reports/physeditworld_50h/requirement_matrix.json"),
    ("completion_audit", "reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json"),
)
POST_MOUNT_COMMANDS = (
    "export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root",
    "bash scripts/migration/write_physeditworld_root_submission_template.sh",
    "bash scripts/migration/validate_physeditworld_root_submission.sh",
    "bash scripts/migration/sample_physeditworld_root_evidence.sh",
    "bash scripts/migration/run_physeditworld_root_onboarding_sequence.sh",
    "bash scripts/migration/write_physeditworld_external_root_handoff_packet.sh",
    "bash scripts/migration/select_physeditworld_root.sh",
    "bash scripts/migration/probe_physeditworld_root_schema.sh",
    "bash scripts/migration/prepare_physeditworld_root_intake.sh",
    "bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh",
    "bash scripts/migration/run_physeditworld_phase0_preflight.sh",
    "python3 -m cam_physgeo.orchestration.physeditworld_backend_readiness",
    "bash scripts/run_physeditworld_pipeline_gates.sh",
    "python3 -m cam_physgeo.orchestration.physeditworld_requirement_matrix",
    "bash scripts/migration/run_physeditworld_completion_audit.sh",
    "bash scripts/migration/run_physeditworld_pai_restore_packet.sh",
    "bash scripts/migration/verify_pai_physeditworld_handoff.sh",
    "bash scripts/migration/run_physeditworld_pai_restore_packet.sh",
)


@dataclass
class DecisionSnapshot:
    name: str
    path: str
    exists: bool
    decision: str
    error_reason: str = ""


@dataclass
class PathSnapshot:
    label: str
    path: str
    exists: bool
    is_dir: bool
    detail: str = ""


def run_text(cmd: list[str], timeout_seconds: int = 10) -> str:
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False, timeout=timeout_seconds)
    except Exception as exc:  # pragma: no cover - host tool defensive path
        return "ERROR:" + repr(exc)
    return proc.stdout.strip()


def read_decision(path: str | Path) -> tuple[str, str]:
    p = Path(path)
    if not p.exists():
        return "MISSING", ""
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return "UNREADABLE", repr(exc)
    return str(obj.get("decision") or obj.get("status") or "UNKNOWN"), ""


def read_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"decision": "UNREADABLE", "error_reason": repr(exc)}
    return obj if isinstance(obj, dict) else {"decision": "UNEXPECTED_JSON"}


def split_roots(raw: str) -> list[str]:
    roots: list[str] = []
    for chunk in raw.replace(",", ":").split(":"):
        item = chunk.strip()
        if item:
            roots.append(item)
    return roots


def path_snapshot(label: str, path: str) -> PathSnapshot:
    p = Path(path)
    if p.exists():
        return PathSnapshot(label=label, path=path, exists=True, is_dir=p.is_dir(), detail="exists")
    return PathSnapshot(label=label, path=path, exists=False, is_dir=False, detail="missing")


def collect_decisions() -> list[DecisionSnapshot]:
    rows: list[DecisionSnapshot] = []
    for name, path in DECISION_PATHS:
        decision, error = read_decision(path)
        rows.append(DecisionSnapshot(name=name, path=path, exists=Path(path).exists(), decision=decision, error_reason=error))
    return rows


def derive_decision(nas: PathSnapshot, roots: list[PathSnapshot]) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if not nas.exists:
        blockers.append("NAS_TARGET_MISSING")
    if not roots:
        blockers.append("PHYS_EDITWORLD_ROOTS_UNSET")
    elif not any(root.exists for root in roots):
        blockers.append("PHYS_EDITWORLD_ROOTS_SET_BUT_NOT_VISIBLE")
    decisions = {row.name: row.decision for row in collect_decisions()}
    if decisions.get("root_candidates") == "PHYS_EDITWORLD_ROOT_CANDIDATES_NONE_STRONG":
        blockers.append("NO_STRONG_ROOT_CANDIDATE_VISIBLE")
    if decisions.get("root_schema_probe") in {"PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT", "MISSING"}:
        blockers.append("ROOT_SCHEMA_PROBE_WAITING_FOR_ROOT")
    if decisions.get("backend_readiness") != "PHYS_EDITWORLD_BACKEND_READY_FOR_BASELINE_WARMUP":
        blockers.append("BACKEND_NOT_READY:" + decisions.get("backend_readiness", "MISSING"))
    if not blockers:
        return "PHYS_EDITWORLD_EXTERNAL_UNBLOCK_PACKET_READY_FOR_POST_MOUNT", blockers
    if not nas.exists or "PHYS_EDITWORLD_ROOTS_UNSET" in blockers or "PHYS_EDITWORLD_ROOTS_SET_BUT_NOT_VISIBLE" in blockers:
        return "PHYS_EDITWORLD_EXTERNAL_UNBLOCK_REQUIRED_NAS_OR_ROOT", blockers
    return "PHYS_EDITWORLD_EXTERNAL_UNBLOCK_REQUIRED_PIPELINE", blockers


def build_packet(nas_target: str) -> dict[str, Any]:
    root_env = os.environ.get("PHYS_EDITWORLD_ROOTS", "")
    roots = [path_snapshot("PHYS_EDITWORLD_ROOTS", root) for root in split_roots(root_env)]
    nas = path_snapshot("NAS target", nas_target)
    decision, blockers = derive_decision(nas, roots)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "blockers": blockers,
        "repo": str(Path.cwd()),
        "git": {
            "branch": run_text(["git", "branch", "--show-current"]),
            "head": run_text(["git", "rev-parse", "--short", "HEAD"]),
            "remote_head": run_text(["git", "rev-parse", "--short", "origin/physion-only-local-assets-videogpa-smoke"]),
        },
        "nas_target": asdict(nas),
        "physeditworld_roots_env": root_env,
        "physeditworld_roots": [asdict(root) for root in roots],
        "required_root_evidence": list(REQUIRED_ROOT_EVIDENCE),
        "decisions": [asdict(row) for row in collect_decisions()],
        "migration_size_summary": read_json("reports/migration/migration_size_summary.json"),
        "post_mount_commands": list(POST_MOUNT_COMMANDS),
        "disk": run_text(["df", "-h", "/home/nvme03", "/home/nvme04", nas_target], timeout_seconds=10),
        "safety": {
            "mode": "CPU/IO only",
            "non_runs": ["no training", "no rollout", "no DPO", "no rsync execute", "no deletion", "no GPU work"],
            "artifact_policy": "Do not push local_assets, videos/images, checkpoints, weights, large logs, or raw migrated data.",
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
        "# PhysEditWorld External Unblock Packet",
        "",
        f"Generated UTC: `{packet['generated_at_utc']}`",
        f"Decision: `{packet['decision']}`",
        "",
        "## Blockers",
        "",
    ]
    if packet["blockers"]:
        for blocker in packet["blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Required Root Evidence", ""])
    for item in packet["required_root_evidence"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## NAS And Root Visibility", ""])
    lines.append(f"- NAS target `{packet['nas_target']['path']}`: `{packet['nas_target']['detail']}`")
    lines.append(f"- `PHYS_EDITWORLD_ROOTS`: `{packet['physeditworld_roots_env'] or 'UNSET'}`")
    if packet["physeditworld_roots"]:
        for root in packet["physeditworld_roots"]:
            lines.append(f"- root `{root['path']}`: `{root['detail']}`")
    size_summary = packet.get("migration_size_summary") or {}
    candidate = size_summary.get("candidate_summary", {}) if isinstance(size_summary, dict) else {}
    approved = size_summary.get("approved_copy_summary", {}) if isinstance(size_summary, dict) else {}
    lines.extend(["", "## Migration Size Snapshot", ""])
    if size_summary:
        lines.append(f"- decision: `{size_summary.get('decision', 'UNKNOWN')}`")
        lines.append(f"- candidate present file bytes: `{candidate.get('present_file_bytes_human', 'unknown')}`")
        lines.append(f"- candidate rows: `{candidate.get('manifest_rows', 'unknown')}`")
        lines.append(f"- directory rows pending recursive sizing: `{candidate.get('dir_rows_pending_recursive_size', 'unknown')}`")
        lines.append(f"- approved rows: `{approved.get('approved_rows', 'unknown')}`")
        lines.append(f"- approved present file bytes: `{approved.get('approved_present_file_bytes', 'unknown')}`")
    else:
        lines.append("- migration size summary missing")
    lines.extend(["", "## Decision Snapshot", ""])
    for row in packet["decisions"]:
        lines.append(f"- `{row['name']}`: `{row['decision']}` (`{row['path']}`)")
    lines.extend(["", "## Post-Mount Commands", "", "```bash"])
    lines.extend(packet["post_mount_commands"])
    lines.extend([
        "```",
        "",
        "## Safety",
        "",
        "This packet is CPU/IO only. It does not copy files, delete files, use GPUs, train, rollout, run DPO, or execute rsync.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Write external NAS/root unblock packet for PhysEditWorld handoff")
    ap.add_argument("--nas_target", default=NAS_TARGET_DEFAULT)
    ap.add_argument("--output_json", default="reports/migration/physeditworld_external_unblock_packet.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_external_unblock_packet.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    packet = build_packet(args.nas_target)
    write_json(packet, args.output_json)
    write_markdown(packet, args.summary)
    print(json.dumps({"decision": packet["decision"], "blockers": packet["blockers"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
