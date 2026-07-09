from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from cam_physgeo.orchestration.physeditworld_root_submission_template import FIELDS, REQUIRED_EVIDENCE

PLACEHOLDER_PREFIX = "<"
READY = "READY_FOR_SCHEMA_PROBE"
PENDING = "PENDING_EXTERNAL_INPUT"
REJECTED_NOT_PHYS = "REJECTED_NOT_PHYS_EDIT_WORLD"
REJECTED_INCOMPLETE = "REJECTED_INCOMPLETE_EVIDENCE"


@dataclass
class ValidationRow:
    row_idx: int
    candidate_root: str
    review_status: str
    status: str
    root_exists: bool
    required_fields_present: bool
    evidence_pass: bool
    missing_required_fields: str = ""
    missing_evidence: str = ""
    skipped_evidence: str = ""
    evidence_counts_json: str = "{}"
    error_reason: str = ""
    next_action: str = ""


def is_placeholder(value: str) -> bool:
    text = (value or "").strip()
    return not text or text.startswith(PLACEHOLDER_PREFIX) or text.endswith(">")


def read_rows(path: str | Path) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return [{key: (row.get(key) or "").strip() for key in FIELDS} for row in reader]


def bounded_glob_count(root: Path, pattern: str, max_matches: int) -> tuple[int, str]:
    if is_placeholder(pattern):
        return 0, "missing"
    if Path(pattern).is_absolute():
        return 0, "absolute_glob_rejected"
    if "**" in pattern:
        return 0, "recursive_glob_rejected"
    try:
        count = 0
        for _ in root.glob(pattern):
            count += 1
            if count >= max_matches:
                break
        return count, "ok"
    except Exception as exc:
        return 0, "glob_error:" + repr(exc)


def validate_row(row_idx: int, row: dict[str, str], max_matches: int) -> ValidationRow:
    candidate_root = row.get("candidate_root", "")
    review_status = row.get("review_status", "") or PENDING
    missing_fields = [field for field in ("candidate_root", *REQUIRED_EVIDENCE) if is_placeholder(row.get(field, ""))]
    required_fields_present = not missing_fields
    root = Path(candidate_root) if candidate_root and not is_placeholder(candidate_root) else None
    root_exists = bool(root and root.exists() and root.is_dir())

    if review_status == REJECTED_NOT_PHYS:
        return ValidationRow(row_idx, candidate_root, review_status, "REJECTED_NOT_PHYS_EDIT_WORLD", root_exists, required_fields_present, False, ";".join(missing_fields), next_action="submit a real PhysEditWorld selected 50h root")
    if not required_fields_present:
        status = "WAITING_FOR_FILLED_TEMPLATE" if review_status == PENDING else "BLOCKED_MISSING_REQUIRED_FIELDS"
        return ValidationRow(row_idx, candidate_root, review_status, status, root_exists, False, False, ";".join(missing_fields), next_action="fill candidate_root plus action/camera/intrinsics/gravity/replay/video globs")
    if not root_exists:
        return ValidationRow(row_idx, candidate_root, review_status, "BLOCKED_ROOT_NOT_VISIBLE", False, True, False, next_action="mount or expose the candidate root on this host")

    counts: dict[str, int] = {}
    missing_evidence: list[str] = []
    skipped_evidence: list[str] = []
    for field in REQUIRED_EVIDENCE:
        count, state = bounded_glob_count(root, row.get(field, ""), max_matches)
        counts[field] = count
        if state != "ok":
            skipped_evidence.append(f"{field}:{state}")
        elif count == 0:
            missing_evidence.append(field)
    evidence_pass = not missing_evidence and not skipped_evidence
    status = READY if evidence_pass and review_status in {PENDING, READY, ""} else "BLOCKED_EVIDENCE_INCOMPLETE"
    if review_status == REJECTED_INCOMPLETE:
        status = REJECTED_INCOMPLETE
    return ValidationRow(
        row_idx=row_idx,
        candidate_root=candidate_root,
        review_status=review_status,
        status=status,
        root_exists=root_exists,
        required_fields_present=True,
        evidence_pass=evidence_pass,
        missing_evidence=";".join(missing_evidence),
        skipped_evidence=";".join(skipped_evidence),
        evidence_counts_json=json.dumps(counts, sort_keys=True),
        next_action="run select/probe/locked handoff" if status == READY else "fix evidence globs or root visibility",
    )


def derive_decision(rows: list[ValidationRow], template_exists: bool) -> str:
    if not template_exists:
        return "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_TEMPLATE_MISSING"
    if any(row.status == READY for row in rows):
        return "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_READY_FOR_SCHEMA_PROBE"
    if rows and all(row.status == "WAITING_FOR_FILLED_TEMPLATE" for row in rows):
        return "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE"
    if rows:
        return "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_BLOCKED"
    return "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_NO_ROWS"


def write_csv(path: str | Path, rows: list[ValidationRow]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(ValidationRow.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(path: str | Path, decision: str, template: str, rows: list[ValidationRow], max_matches: int) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "template": template,
        "rows": [asdict(row) for row in rows],
        "ready_rows": sum(1 for row in rows if row.status == READY),
        "max_matches_per_evidence_glob": max_matches,
        "safety": {
            "mode": "CPU/IO only",
            "no_recursive_globs": True,
            "does_not_copy_delete_train_or_use_gpu": True,
            "does_not_select_or_lock_root": True,
        },
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: str | Path, decision: str, rows: list[ValidationRow]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    lines = ["# PhysEditWorld Root Submission Validation", "", f"Decision: `{decision}`", "", "## Status Counts", ""]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    if not counts:
        lines.append("- none")
    lines.extend(["", "## Rows", ""])
    for row in rows:
        lines.append(f"- row `{row.row_idx}`: `{row.status}` root=`{row.candidate_root or 'EMPTY'}`")
        if row.missing_required_fields:
            lines.append(f"  - missing fields: `{row.missing_required_fields}`")
        if row.missing_evidence:
            lines.append(f"  - missing evidence: `{row.missing_evidence}`")
        if row.skipped_evidence:
            lines.append(f"  - skipped evidence: `{row.skipped_evidence}`")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    lines.extend([
        "", "## Safety", "",
        "This validator is CPU/IO only. It reads the filled TSV and bounded non-recursive evidence globs. It does not copy files, delete files, approve migration rows, select/lock a root, use GPUs, train, rollout, evaluate videos, or run DPO.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Validate a filled PhysEditWorld selected-root submission TSV")
    ap.add_argument("--template", default="reports/migration/physeditworld_root_submission_template.tsv")
    ap.add_argument("--output_csv", default="reports/migration/physeditworld_root_submission_validation.csv")
    ap.add_argument("--output_json", default="reports/migration/physeditworld_root_submission_validation.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_root_submission_validation.md")
    ap.add_argument("--max_matches_per_glob", type=int, default=25)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    template_exists = Path(args.template).exists()
    rows = [validate_row(i + 1, row, args.max_matches_per_glob) for i, row in enumerate(read_rows(args.template))]
    decision = derive_decision(rows, template_exists)
    write_csv(args.output_csv, rows)
    write_json(args.output_json, decision, args.template, rows, args.max_matches_per_glob)
    write_markdown(args.summary, decision, rows)
    print(json.dumps({"decision": decision, "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
