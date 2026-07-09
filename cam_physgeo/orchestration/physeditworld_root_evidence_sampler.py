from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from cam_physgeo.orchestration.physeditworld_root_submission_template import FIELDS, REQUIRED_EVIDENCE
from cam_physgeo.orchestration.physeditworld_root_submission_validate import is_placeholder, read_rows


@dataclass
class EvidenceSample:
    row_idx: int
    evidence_field: str
    candidate_root: str
    submitted_glob: str
    sample_path: str
    relative_path: str
    exists: bool
    is_file: bool
    size_bytes: int | None
    status: str
    error_reason: str = ""


def safe_sample_glob(root: Path, pattern: str, limit: int) -> tuple[list[Path], str]:
    if is_placeholder(pattern):
        return [], "MISSING_GLOB"
    if Path(pattern).is_absolute():
        return [], "ABSOLUTE_GLOB_REJECTED"
    if "**" in pattern:
        return [], "RECURSIVE_GLOB_REJECTED"
    try:
        matches: list[Path] = []
        for path in sorted(root.glob(pattern)):
            matches.append(path)
            if len(matches) >= limit:
                break
        if not matches:
            return [], "NO_MATCHES"
        return matches, "PASS"
    except Exception as exc:
        return [], "GLOB_ERROR:" + repr(exc)


def sample_row(row_idx: int, row: dict[str, str], samples_per_field: int) -> list[EvidenceSample]:
    candidate_root = row.get("candidate_root", "")
    if is_placeholder(candidate_root):
        return [EvidenceSample(row_idx, "candidate_root", candidate_root, "", "", "", False, False, None, "WAITING_FOR_FILLED_TEMPLATE", "candidate_root is empty or placeholder")]
    root = Path(candidate_root)
    if not root.exists() or not root.is_dir():
        return [EvidenceSample(row_idx, "candidate_root", candidate_root, "", str(root), "", root.exists(), False, None, "ROOT_NOT_VISIBLE")]

    out: list[EvidenceSample] = []
    for field in REQUIRED_EVIDENCE:
        pattern = row.get(field, "")
        matches, status = safe_sample_glob(root, pattern, samples_per_field)
        if not matches:
            out.append(EvidenceSample(row_idx, field, candidate_root, pattern, "", "", False, False, None, status))
            continue
        for match in matches:
            try:
                rel = str(match.relative_to(root))
            except Exception:
                rel = str(match)
            size = match.stat().st_size if match.is_file() else None
            out.append(EvidenceSample(row_idx, field, candidate_root, pattern, str(match), rel, match.exists(), match.is_file(), size, "PASS"))
    return out


def derive_decision(rows: list[EvidenceSample]) -> str:
    if not rows:
        return "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_NO_ROWS"
    if all(row.status == "WAITING_FOR_FILLED_TEMPLATE" for row in rows):
        return "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE"
    if any(row.status == "ROOT_NOT_VISIBLE" for row in rows):
        return "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_BLOCKED_ROOT_NOT_VISIBLE"
    pass_fields = {row.evidence_field for row in rows if row.status == "PASS"}
    if set(REQUIRED_EVIDENCE).issubset(pass_fields):
        return "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_READY_FOR_SCHEMA_PROBE"
    return "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_BLOCKED_INCOMPLETE_EVIDENCE"


def write_csv(path: str | Path, rows: list[EvidenceSample]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(EvidenceSample.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(path: str | Path, decision: str, rows: list[EvidenceSample], template: str, samples_per_field: int) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "template": template,
        "samples_per_field": samples_per_field,
        "samples": [asdict(row) for row in rows],
        "pass_samples": sum(1 for row in rows if row.status == "PASS"),
        "safety": {
            "mode": "CPU/IO only",
            "bounded_samples_per_field": samples_per_field,
            "no_recursive_globs": True,
            "does_not_copy_delete_train_or_use_gpu": True,
        },
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: str | Path, decision: str, rows: list[EvidenceSample]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    lines = ["# PhysEditWorld Root Evidence Sampler", "", f"Decision: `{decision}`", "", "## Status Counts", ""]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    if not counts:
        lines.append("- none")
    lines.extend(["", "## Samples", ""])
    for row in rows[:80]:
        lines.append(f"- row `{row.row_idx}` / `{row.evidence_field}`: `{row.status}`")
        if row.relative_path:
            lines.append(f"  - sample: `{row.relative_path}`")
        if row.size_bytes is not None:
            lines.append(f"  - size_bytes: `{row.size_bytes}`")
        if row.error_reason:
            lines.append(f"  - error: {row.error_reason}")
    if len(rows) > 80:
        lines.append(f"- truncated in markdown: {len(rows) - 80} additional samples are in CSV/JSON")
    lines.extend(["", "## Safety", "", "This sampler reads the filled root-submission TSV and bounded non-recursive evidence globs. It records example paths and sizes only. It does not copy files, delete files, approve migration rows, select/lock a root, use GPUs, train, rollout, evaluate videos, or run DPO."])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sample concrete evidence paths from a filled PhysEditWorld selected-root submission TSV")
    ap.add_argument("--template", default="reports/migration/physeditworld_root_submission_template.tsv")
    ap.add_argument("--samples_per_field", type=int, default=3)
    ap.add_argument("--output_csv", default="reports/migration/physeditworld_root_evidence_samples.csv")
    ap.add_argument("--output_json", default="reports/migration/physeditworld_root_evidence_samples.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_root_evidence_samples.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    all_samples: list[EvidenceSample] = []
    for idx, row in enumerate(read_rows(args.template), start=1):
        all_samples.extend(sample_row(idx, row, args.samples_per_field))
    decision = derive_decision(all_samples)
    write_csv(args.output_csv, all_samples)
    write_json(args.output_json, decision, all_samples, args.template, args.samples_per_field)
    write_markdown(args.summary, decision, all_samples)
    print(json.dumps({"decision": decision, "samples": len(all_samples)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
