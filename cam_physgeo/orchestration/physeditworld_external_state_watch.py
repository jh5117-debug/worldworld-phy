from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_NAS = "/mnt/workspace/hj/nas_hj"
REPORTS = (
    ("external_root_handoff", "reports/migration/physeditworld_external_root_handoff_packet.json"),
    ("root_onboarding", "reports/migration/physeditworld_root_onboarding_sequence.json"),
    ("root_validation", "reports/migration/physeditworld_root_submission_validation.json"),
    ("root_evidence_samples", "reports/migration/physeditworld_root_evidence_samples.json"),
    ("root_selection", "reports/migration/physeditworld_selected_root_status.json"),
    ("root_schema_probe", "reports/migration/physeditworld_root_schema_probe.json"),
    ("pai_handoff", "reports/migration/pai_handoff_status.json"),
    ("requirement_matrix", "reports/physeditworld_50h/requirement_matrix.json"),
)


@dataclass
class WatchRow:
    name: str
    status: str
    detail: str
    next_action: str = ""


def split_roots(raw: str) -> list[str]:
    if not raw.strip():
        return []
    roots: list[str] = []
    for part in raw.replace(",", os.pathsep).split(os.pathsep):
        part = part.strip()
        if part:
            roots.append(part)
    return roots


def read_decision(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return "MISSING"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return "UNREADABLE:" + repr(exc)
    return str(obj.get("decision") or obj.get("status") or "UNKNOWN")


def build_rows(nas_target: str, roots_env: str) -> list[WatchRow]:
    rows: list[WatchRow] = []
    nas_exists = Path(nas_target).exists()
    rows.append(WatchRow("nas_target", "PASS" if nas_exists else "BLOCKED", f"{nas_target} exists={nas_exists}", "mount or expose NAS target" if not nas_exists else "continue"))
    roots = split_roots(roots_env)
    visible_roots = [root for root in roots if Path(root).exists() and Path(root).is_dir()]
    if not roots:
        rows.append(WatchRow("physeditworld_roots_env", "BLOCKED", "PHYS_EDITWORLD_ROOTS is unset", "export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root"))
    elif not visible_roots:
        rows.append(WatchRow("physeditworld_roots_env", "BLOCKED", f"roots set but not visible: {roots}", "mount or correct PHYS_EDITWORLD_ROOTS"))
    else:
        rows.append(WatchRow("physeditworld_roots_env", "PASS", f"visible roots: {visible_roots}", "run root selection/schema probe"))
    for name, path in REPORTS:
        decision = read_decision(path)
        status = "PASS" if any(token in decision for token in ("READY", "WAITING", "PASS")) else "BLOCKED"
        if name in {"root_selection", "root_schema_probe", "pai_handoff", "requirement_matrix"} and "WAITING" in decision:
            status = "BLOCKED"
        rows.append(WatchRow(name, status, f"{path}: {decision}", next_action_for(name, decision)))
    return rows


def next_action_for(name: str, decision: str) -> str:
    if name == "external_root_handoff" and "WAITING_FOR_FILLED_TEMPLATE" in decision:
        return "fill reports/migration/physeditworld_root_submission_template.tsv"
    if name == "root_onboarding" and "READY_FOR_SCHEMA_PROBE" in decision:
        return "set PHYS_EDITWORLD_ROOTS and run select/probe/locked handoff"
    if name == "root_selection" and "LOCKED" not in decision:
        return "run scripts/migration/select_physeditworld_root.sh after root is visible"
    if name == "root_schema_probe" and "READY_FOR_MANIFEST_AUDIT" not in decision:
        return "run scripts/migration/probe_physeditworld_root_schema.sh after root lock"
    if "MISSING" in decision:
        return "run the corresponding report writer"
    if "BLOCKED" in decision or "REQUIRED" in decision:
        return "fix the blocker recorded in the report"
    return "continue"


def derive_decision(rows: list[WatchRow]) -> str:
    lookup = {row.name: row for row in rows}
    if lookup.get("nas_target") and lookup["nas_target"].status != "PASS":
        return "PHYS_EDITWORLD_EXTERNAL_STATE_WAITING_FOR_NAS"
    if lookup.get("physeditworld_roots_env") and lookup["physeditworld_roots_env"].status != "PASS":
        return "PHYS_EDITWORLD_EXTERNAL_STATE_WAITING_FOR_ROOT_ENV"
    handoff = lookup.get("external_root_handoff")
    if handoff and "WAITING_FOR_FILLED_TEMPLATE" in handoff.detail:
        return "PHYS_EDITWORLD_EXTERNAL_STATE_WAITING_FOR_FILLED_TEMPLATE"
    if all(row.status == "PASS" for row in rows[:4]):
        return "PHYS_EDITWORLD_EXTERNAL_STATE_READY_FOR_ROOT_SELECTION"
    return "PHYS_EDITWORLD_EXTERNAL_STATE_BLOCKED"


def write_json(path: str | Path, decision: str, rows: list[WatchRow], nas_target: str, roots_env: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "nas_target": nas_target,
        "physeditworld_roots_env": roots_env,
        "rows": [asdict(row) for row in rows],
        "safe_next_commands": [
            "bash scripts/migration/write_physeditworld_external_root_handoff_packet.sh",
            "bash scripts/migration/run_physeditworld_root_onboarding_sequence.sh",
            "export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root",
            "bash scripts/migration/select_physeditworld_root.sh",
            "bash scripts/migration/probe_physeditworld_root_schema.sh",
        ],
        "safety": {"mode": "CPU/IO only", "does_not_copy_delete_train_or_use_gpu": True},
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: str | Path, decision: str, rows: list[WatchRow]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# PhysEditWorld External State Watch", "", f"Decision: `{decision}`", "", "## Rows", ""]
    for row in rows:
        lines.append(f"- `{row.name}`: `{row.status}`")
        lines.append(f"  - detail: {row.detail}")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    lines.extend([
        "", "## Safety", "",
        "This watcher is one-shot CPU/IO only. It reads environment/path visibility plus existing JSON reports. It does not copy files, delete files, use GPUs, train, rollout, evaluate videos, run DPO, or select/lock a root.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Watch external state required for PhysEditWorld selected-root onboarding")
    ap.add_argument("--nas_target", default=DEFAULT_NAS)
    ap.add_argument("--physeditworld_roots", default="")
    ap.add_argument("--output_json", default="reports/migration/physeditworld_external_state_watch.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_external_state_watch.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    roots_env = args.physeditworld_roots or os.environ.get("PHYS_EDITWORLD_ROOTS", "")
    rows = build_rows(args.nas_target, roots_env)
    decision = derive_decision(rows)
    write_json(args.output_json, decision, rows, args.nas_target, roots_env)
    write_markdown(args.summary, decision, rows)
    print(json.dumps({"decision": decision, "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
