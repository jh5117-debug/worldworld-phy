from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class RootIntakeStatus:
    name: str
    status: str
    decision: str = ""
    path: str = ""
    detail: str = ""
    next_action: str = ""


def read_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"decision": "UNREADABLE", "error": repr(exc)}


def decision_of(path: str | Path) -> str:
    obj = read_json(path)
    return str(obj.get("decision") or obj.get("status") or "MISSING")


def count_jsonl(path: str | Path) -> int | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def split_roots(raw: str) -> list[str]:
    if not raw.strip():
        return []
    out: list[str] = []
    for part in raw.replace(",", os.pathsep).split(os.pathsep):
        part = part.strip()
        if part:
            out.append(part)
    return out


def build_statuses(args: argparse.Namespace) -> tuple[str, list[RootIntakeStatus]]:
    roots = split_roots(args.physeditworld_roots or os.environ.get("PHYS_EDITWORLD_ROOTS", ""))
    root_candidates_decision = decision_of(args.root_candidates_json)
    root_selection_decision = decision_of(args.root_selection_json)
    locked_handoff_decision = decision_of(args.locked_handoff_json)
    pai_handoff_decision = decision_of(args.pai_handoff_json)
    completion_decision = decision_of(args.completion_json)
    all_rows = count_jsonl(args.strict_manifest)
    train_rows = count_jsonl(args.train_manifest)
    lingbot_rows = count_jsonl(args.lingbot_train_manifest)

    rows = [
        RootIntakeStatus(
            "root_candidates",
            "PASS" if root_candidates_decision == "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG" else "BLOCKED",
            root_candidates_decision,
            args.root_candidates_json,
            "candidate ranker sees a strong root" if root_candidates_decision == "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG" else "no automatically usable PhysEditWorld selected-50h root is visible",
            "mount/provide the real selected 50h root and set PHYS_EDITWORLD_ROOTS",
        ),
        RootIntakeStatus(
            "root_input",
            "PASS" if roots and all(Path(root).exists() for root in roots) else "BLOCKED",
            "ROOTS_VISIBLE" if roots and all(Path(root).exists() for root in roots) else "ROOTS_MISSING_OR_UNSET",
            ";".join(roots),
            f"roots={len(roots)}",
            "export PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h",
        ),
        RootIntakeStatus(
            "root_selection_lock",
            "PASS" if root_selection_decision == "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED" else "BLOCKED",
            root_selection_decision,
            args.root_selection_json,
            "selected-root lock exists" if root_selection_decision == "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED" else "root lock not written",
            "PHYS_EDITWORLD_ROOTS=/path/to/root bash scripts/migration/select_physeditworld_root.sh",
        ),
        RootIntakeStatus(
            "locked_handoff",
            "PASS" if locked_handoff_decision == "LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE" else "BLOCKED",
            locked_handoff_decision,
            args.locked_handoff_json,
            "post-mount handoff is complete" if locked_handoff_decision == "LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE" else "safe locked handoff is not complete",
            "PHYS_EDITWORLD_ROOTS=/path/to/root bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh",
        ),
        RootIntakeStatus(
            "pai_handoff",
            "PASS" if pai_handoff_decision == "PAI_HANDOFF_READY_FOR_POST_MOUNT_CONTINUE" else "BLOCKED",
            pai_handoff_decision,
            args.pai_handoff_json,
            "PAI handoff is ready" if pai_handoff_decision == "PAI_HANDOFF_READY_FOR_POST_MOUNT_CONTINUE" else "NAS/root/manifests not all ready",
            "mount NAS/root and rerun verify_pai_physeditworld_handoff.sh",
        ),
        RootIntakeStatus(
            "strict_manifest_rows",
            "PASS" if (all_rows or 0) > 0 and (train_rows or 0) > 0 else "BLOCKED",
            "STRICT_ROWS_READY" if (all_rows or 0) > 0 and (train_rows or 0) > 0 else "STRICT_ROWS_EMPTY",
            f"{args.strict_manifest};{args.train_manifest}",
            f"all={all_rows if all_rows is not None else 'missing'} train={train_rows if train_rows is not None else 'missing'}",
            "run manifest audit and replay-group split after root lock",
        ),
        RootIntakeStatus(
            "lingbot_train_rows",
            "PASS" if (lingbot_rows or 0) > 0 else "BLOCKED",
            "LINGBOT_ROWS_READY" if (lingbot_rows or 0) > 0 else "LINGBOT_ROWS_EMPTY",
            args.lingbot_train_manifest,
            f"rows={lingbot_rows if lingbot_rows is not None else 'missing'}",
            "run prompt-only gravity conversion after strict split",
        ),
        RootIntakeStatus(
            "completion_audit",
            "PASS" if completion_decision == "PHYS_EDITWORLD_OBJECTIVE_COMPLETE" else "BLOCKED",
            completion_decision,
            args.completion_json,
            "full objective complete" if completion_decision == "PHYS_EDITWORLD_OBJECTIVE_COMPLETE" else "objective remains incomplete",
            "bash scripts/migration/run_physeditworld_completion_audit.sh",
        ),
    ]

    if root_selection_decision == "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED":
        decision = "PHYS_EDITWORLD_ROOT_INTAKE_LOCKED_READY_FOR_HANDOFF"
    elif roots:
        decision = "PHYS_EDITWORLD_ROOT_INTAKE_ROOTS_PROVIDED_NEED_LOCK"
    else:
        decision = "PHYS_EDITWORLD_ROOT_INTAKE_WAITING_FOR_EXTERNAL_ROOT"
    return decision, rows


def write_json(path: str | Path, decision: str, rows: list[RootIntakeStatus]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "checks": [asdict(row) for row in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(path: str | Path, decision: str, rows: list[RootIntakeStatus]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PhysEditWorld Root Intake Handoff",
        "",
        f"Decision: `{decision}`",
        "",
        "## Required External Input",
        "",
        "Provide the real PhysEditWorld selected 50h root and expose it on H20/PAI as a directory containing structural evidence:",
        "",
        "- action trace files",
        "- camera trajectory / poses",
        "- intrinsics / calibration",
        "- gravity labels",
        "- replay-group or matched-replay metadata",
        "- target videos / frames",
        "",
        "Do not provide VideoPHY/Wan result folders, model checkpoints, old PhysInOne conditions, contact sheets, or prompt-derived MP4 folders as the selected root.",
        "",
        "## Current Checks",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row.name}`: `{row.status}` / `{row.decision}`")
        if row.path:
            lines.append(f"  - path: `{row.path}`")
        if row.detail:
            lines.append(f"  - detail: {row.detail}")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    lines.extend([
        "",
        "## Safe Resume Commands",
        "",
        "```bash",
        "cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys",
        "export PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h",
        "bash scripts/migration/select_physeditworld_root.sh",
        "PHYS_EDITWORLD_ROOTS=$PHYS_EDITWORLD_ROOTS bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh",
        "bash scripts/migration/run_physeditworld_completion_audit.sh",
        "```",
        "",
        "## Safety",
        "",
        "This intake report is CPU/IO only. It does not copy files, delete files, use GPUs, train, rollout, evaluate videos, or run DPO.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Build a PhysEditWorld selected-root intake handoff report")
    ap.add_argument("--physeditworld_roots", default="")
    ap.add_argument("--root_candidates_json", default="reports/migration/physeditworld_root_candidates_ranked.json")
    ap.add_argument("--root_selection_json", default="reports/migration/physeditworld_selected_root_status.json")
    ap.add_argument("--locked_handoff_json", default="reports/migration/locked_handoff_sequence.json")
    ap.add_argument("--pai_handoff_json", default="reports/migration/pai_handoff_status.json")
    ap.add_argument("--completion_json", default="reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json")
    ap.add_argument("--strict_manifest", default="manifests/physeditworld_50h_all.jsonl")
    ap.add_argument("--train_manifest", default="manifests/physeditworld_50h_train.jsonl")
    ap.add_argument("--lingbot_train_manifest", default="manifests/physeditworld_50h_lingbot_train.jsonl")
    ap.add_argument("--output_json", default="reports/migration/physeditworld_root_intake.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_root_intake.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    decision, rows = build_statuses(args)
    write_json(args.output_json, decision, rows)
    write_summary(args.summary, decision, rows)
    print(json.dumps({"decision": decision, "checks": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
