from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from cam_physgeo.data.physeditworld_root_candidates import RootCandidate, rank_candidates, parse_roots


@dataclass
class RootSelection:
    root: str
    status: str
    score: int = 0
    signals: str = ""
    exists: bool = False
    is_dir: bool = False
    evidence: str = ""
    error_reason: str = ""
    next_action: str = ""


def evaluate_roots(raw_roots: str, allow_weak: bool, max_depth: int, max_files: int) -> tuple[str, list[RootSelection], list[RootCandidate]]:
    roots = parse_roots(raw_roots)
    if not roots:
        return "PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT", [RootSelection("", "BLOCKED", error_reason="PHYS_EDITWORLD_ROOTS is empty", next_action="set PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h")], []
    ranked = rank_candidates([], roots, max_depth=max_depth, max_files=max_files)
    by_root = {row.root: row for row in ranked}
    selections: list[RootSelection] = []
    missing = False
    weak = False
    rejected = False
    for root in roots:
        row = by_root.get(root)
        if row is None:
            selections.append(RootSelection(root, "BLOCKED", error_reason="root was not ranked", next_action="rerun root candidate ranker"))
            rejected = True
            continue
        if not row.exists or not row.is_dir:
            missing = True
            selections.append(RootSelection(root, "BLOCKED", row.score, row.signals, row.exists, row.is_dir, row.evidence, "root missing or not a directory", "mount/provide this root path"))
        elif row.status == "STRONG_CANDIDATE":
            selections.append(RootSelection(root, "LOCKED", row.score, row.signals, row.exists, row.is_dir, row.evidence, next_action="run post-mount continuation"))
        elif row.status == "WEAK_CANDIDATE" and allow_weak:
            weak = True
            selections.append(RootSelection(root, "REVIEW_LOCKED", row.score, row.signals, row.exists, row.is_dir, row.evidence, "weak candidate accepted only because --allow_weak was set", "manual review required before training/rollout"))
        elif row.status == "WEAK_CANDIDATE":
            weak = True
            selections.append(RootSelection(root, "BLOCKED", row.score, row.signals, row.exists, row.is_dir, row.evidence, "candidate is weak, not enough action/camera/intrinsics/gravity/replay/video evidence", "provide stronger root or rerun with --allow_weak only for manual inspection"))
        else:
            rejected = True
            selections.append(RootSelection(root, "BLOCKED", row.score, row.signals, row.exists, row.is_dir, row.evidence, "candidate rejected as likely false positive", "do not use this root"))
    if missing:
        return "PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_ROOT_MISSING", selections, ranked
    if rejected:
        return "PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_REJECTED_ROOT", selections, ranked
    if weak and not allow_weak:
        return "PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_WEAK_ROOT", selections, ranked
    if weak and allow_weak:
        return "PHYS_EDITWORLD_ROOT_SELECTION_REVIEW_REQUIRED", selections, ranked
    return "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED", selections, ranked


def write_csv(rows: list[RootSelection], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(RootSelection.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(decision: str, rows: list[RootSelection], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "selected_roots": [asdict(r) for r in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def maybe_write_lock(decision: str, rows: list[RootSelection], lock_path: str | Path) -> None:
    p = Path(lock_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if decision != "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED":
        if p.exists():
            p.unlink()
        return
    payload = {
        "decision": decision,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "roots": [asdict(r) for r in rows],
        "safety": "Root selection only. This lock does not imply manifest audit, conversion, training, rollout, or DPO has run.",
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(decision: str, rows: list[RootSelection], lock_path: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# PhysEditWorld Selected Root Status", "", f"Decision: `{decision}`", "", "## Roots", ""]
    for row in rows:
        loc = f" `{row.root}`" if row.root else ""
        lines.append(f"- `{row.status}`{loc}")
        lines.append(f"  - score: {row.score}")
        lines.append(f"  - exists/is_dir: {row.exists}/{row.is_dir}")
        lines.append(f"  - signals: {row.signals or 'none'}")
        if row.evidence:
            lines.append(f"  - evidence: {row.evidence}")
        if row.error_reason:
            lines.append(f"  - blocker: {row.error_reason}")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    lines.extend(["", "## Lock", "", f"- lock path: `{lock_path}`"])
    if decision == "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED":
        lines.append("- lock written: yes")
    else:
        lines.append("- lock written: no")
    lines.extend([
        "",
        "## Next Commands",
        "",
        "```bash",
        "PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h bash scripts/migration/select_physeditworld_root.sh",
        "PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h bash scripts/continue_physeditworld_after_mount.sh",
        "```",
        "",
        "## Safety",
        "",
        "This selector is CPU/IO only. It does not copy data, delete files, train, rollout, run DPO, use GPUs, or push large artifacts.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Select and lock a strong PhysEditWorld 50h root")
    ap.add_argument("--roots", default="", help="Colon/comma-separated root list. Defaults to PHYS_EDITWORLD_ROOTS.")
    ap.add_argument("--allow_weak", action="store_true", help="Allow weak roots for manual review only; does not produce PASS lock.")
    ap.add_argument("--max_depth", type=int, default=3)
    ap.add_argument("--max_files_per_root", type=int, default=1000)
    ap.add_argument("--output_csv", default="reports/migration/physeditworld_selected_root_status.csv")
    ap.add_argument("--output_json", default="reports/migration/physeditworld_selected_root_status.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_selected_root_status.md")
    ap.add_argument("--lock", default="reports/migration/physeditworld_selected_root.lock.json")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw_roots = args.roots or os.environ.get("PHYS_EDITWORLD_ROOTS", "")
    decision, rows, _ranked = evaluate_roots(raw_roots, args.allow_weak, args.max_depth, args.max_files_per_root)
    write_csv(rows, args.output_csv)
    write_json(decision, rows, args.output_json)
    maybe_write_lock(decision, rows, args.lock)
    write_summary(decision, rows, args.lock, args.summary)
    print(json.dumps({"decision": decision, "roots": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
