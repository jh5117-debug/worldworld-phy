from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class CopyPlanRow:
    manifest_kind: str
    row_index: int
    category: str
    manifest_path: str
    resolved_target: str
    copy_source: str
    destination_subdir: str
    exists: bool
    file_type: str
    size_bytes: str
    sha256_status: str
    sha256: str
    copy_recommendation: str
    approved: str
    approval_reason: str
    copy_status: str
    notes: str


def read_tsv(path: str | Path) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def boolish(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def row_status(row: dict[str, str], source: Path) -> str:
    if not source.exists():
        return "BLOCKED_MISSING_ON_H20"
    if str(source).startswith("local_assets/") or "/local_assets/" in str(source):
        return "BLOCKED_LOCAL_ASSETS_EXCLUDED"
    if row.get("file_type") == "dir":
        return "NEEDS_REVIEW_DIR"
    return "NEEDS_REVIEW_FILE"


def build_plan_rows(manifest_kind: str, manifest_path: str | Path) -> list[CopyPlanRow]:
    out: list[CopyPlanRow] = []
    destination = "weights" if manifest_kind == "weights" else "data"
    for idx, row in enumerate(read_tsv(manifest_path), start=1):
        source_text = row.get("resolved_target") or row.get("path", "")
        source = Path(source_text) if source_text else Path("__missing_path__")
        status = row_status(row, source) if source_text else "BLOCKED_EMPTY_SOURCE"
        out.append(CopyPlanRow(
            manifest_kind=manifest_kind,
            row_index=idx,
            category=row.get("category", ""),
            manifest_path=row.get("path", ""),
            resolved_target=row.get("resolved_target", ""),
            copy_source=source_text,
            destination_subdir=destination,
            exists=str(source.exists()),
            file_type=row.get("file_type", ""),
            size_bytes=row.get("size_bytes", ""),
            sha256_status=row.get("sha256_status", ""),
            sha256=row.get("sha256", ""),
            copy_recommendation=row.get("copy_recommendation", ""),
            approved="false",
            approval_reason="requires explicit human/Codex review before copying",
            copy_status=status,
            notes=row.get("notes", ""),
        ))
    return out


def write_tsv(rows: Iterable[CopyPlanRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(CopyPlanRow.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def summarize(rows: list[CopyPlanRow]) -> dict[str, object]:
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_file_type: dict[str, int] = {}
    approved = 0
    for row in rows:
        by_kind[row.manifest_kind] = by_kind.get(row.manifest_kind, 0) + 1
        by_status[row.copy_status] = by_status.get(row.copy_status, 0) + 1
        by_file_type[row.file_type] = by_file_type.get(row.file_type, 0) + 1
        if boolish(row.approved):
            approved += 1
    decision = "COPY_PLAN_READY_FOR_APPROVAL" if rows else "COPY_PLAN_EMPTY"
    if approved == 0:
        decision = "COPY_PLAN_REVIEW_REQUIRED"
    return {
        "decision": decision,
        "rows": len(rows),
        "approved_rows": approved,
        "by_kind": by_kind,
        "by_status": by_status,
        "by_file_type": by_file_type,
        "safety": {
            "copied_files": False,
            "deleted_files": False,
            "default_approved": False,
            "requires_explicit_approval": True,
        },
    }


def write_json(summary: dict[str, object], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(summary: dict[str, object], tsv_path: str | Path, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PhysEditWorld Migration Copy Plan Template",
        "",
        f"Decision: `{summary['decision']}`",
        "",
        "## Safety",
        "",
        "- This is a review template, not an execute list.",
        "- Every row is generated with `approved=false` by default.",
        "- No data, weights, checkpoints, or local_assets were copied.",
        "- No files were deleted.",
        "",
        "## Outputs",
        "",
        f"- TSV: `{tsv_path}`",
        "",
        "## Counts",
        "",
        f"- Rows: `{summary['rows']}`",
        f"- Approved rows: `{summary['approved_rows']}`",
        "",
        "### By Kind",
        "",
    ]
    for key, value in sorted(summary["by_kind"].items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "### By Copy Status", ""])
    for key, value in sorted(summary["by_status"].items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend([
        "",
        "## Next Action",
        "",
        "Review this template after the NAS and selected PhysEditWorld 50h root are visible. Only rows that are truly necessary for restore should be changed to `approved=true`; old rollouts, contact sheets, failed checkpoints, and broad `local_assets/` payloads must remain excluded.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Build an explicit no-default-approval migration copy plan template")
    ap.add_argument("--weights_manifest", default="reports/migration/required_weights_manifest.tsv")
    ap.add_argument("--data_manifest", default="reports/migration/required_data_manifest.tsv")
    ap.add_argument("--output_tsv", default="reports/migration/approved_copy_manifest_template.tsv")
    ap.add_argument("--output_json", default="reports/migration/approved_copy_manifest_template.json")
    ap.add_argument("--summary", default="reports/migration/approved_copy_manifest_template_summary.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = []
    rows.extend(build_plan_rows("weights", args.weights_manifest))
    rows.extend(build_plan_rows("data", args.data_manifest))
    write_tsv(rows, args.output_tsv)
    summary = summarize(rows)
    write_json(summary, args.output_json)
    write_summary(summary, args.output_tsv, args.summary)
    print(json.dumps({"decision": summary["decision"], "rows": summary["rows"], "approved_rows": summary["approved_rows"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
