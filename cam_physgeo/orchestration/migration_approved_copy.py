from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ApprovedCopyRow:
    row_index: int
    manifest_kind: str
    copy_source: str
    destination_subdir: str
    destination_path: str
    approved: str
    copy_status: str
    command: str = ""
    error_reason: str = ""


def boolish(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def read_plan(path: str | Path) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def safe_destination(root: Path, subdir: str, source: Path) -> Path:
    name = source.name or "unnamed_asset"
    return root / subdir / name


def build_rows(plan_path: str | Path, migration_root: str | Path) -> list[ApprovedCopyRow]:
    root = Path(migration_root)
    rows: list[ApprovedCopyRow] = []
    for idx, row in enumerate(read_plan(plan_path), start=1):
        approved = row.get("approved", "false")
        if not boolish(approved):
            continue
        source_text = row.get("copy_source", "")
        source = Path(source_text) if source_text else Path("__missing_source__")
        subdir = row.get("destination_subdir") or row.get("manifest_kind") or "assets"
        dest = safe_destination(root, subdir, source)
        if not source_text:
            status = "BLOCKED_EMPTY_SOURCE"
            error = "copy_source empty"
        elif str(source).startswith("local_assets/") or "/local_assets/" in str(source):
            status = "BLOCKED_LOCAL_ASSETS_EXCLUDED"
            error = "local_assets payloads are forbidden"
        elif not source.exists():
            status = "BLOCKED_SOURCE_MISSING"
            error = "source not found on H20"
        else:
            status = "PENDING_APPROVED_COPY"
            error = ""
        rows.append(ApprovedCopyRow(
            row_index=idx,
            manifest_kind=row.get("manifest_kind", ""),
            copy_source=source_text,
            destination_subdir=subdir,
            destination_path=str(dest),
            approved=approved,
            copy_status=status,
            error_reason=error,
        ))
    return rows


def run_rsync(row: ApprovedCopyRow, dry_run: bool) -> ApprovedCopyRow:
    dest_parent = Path(row.destination_path).parent
    dest_parent.mkdir(parents=True, exist_ok=True)
    cmd = ["rsync", "-aH", "--info=progress2", row.copy_source, str(dest_parent) + "/"]
    if dry_run:
        cmd.insert(1, "--dry-run")
    row.command = " ".join(shlex.quote(x) for x in cmd)
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if proc.returncode == 0:
        row.copy_status = "DRYRUN_OK" if dry_run else "COPIED"
        row.error_reason = ""
    else:
        row.copy_status = "DRYRUN_FAILED" if dry_run else "COPY_FAILED"
        row.error_reason = proc.stdout[-1000:]
    return row


def write_csv(rows: list[ApprovedCopyRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(ApprovedCopyRow.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def decision_for(rows: list[ApprovedCopyRow], migration_root: Path, execute: bool) -> str:
    if not rows:
        return "APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS"
    if execute and os.environ.get("MIGRATION_APPROVED") != "1":
        return "APPROVED_COPY_BLOCKED_MIGRATION_APPROVED_ENV"
    if execute and os.environ.get("MIGRATION_COPY_APPROVED") != "1":
        return "APPROVED_COPY_BLOCKED_COPY_APPROVED_ENV"
    if execute and not migration_root.exists():
        return "APPROVED_COPY_BLOCKED_NAS_MISSING"
    if any(row.copy_status.startswith("BLOCKED") for row in rows):
        return "APPROVED_COPY_BLOCKED_ROW_VALIDATION"
    if not execute:
        return "APPROVED_COPY_DRYRUN_READY"
    if all(row.copy_status == "COPIED" for row in rows):
        return "APPROVED_COPY_EXECUTED"
    return "APPROVED_COPY_PARTIAL_OR_FAILED"


def write_summary(rows: list[ApprovedCopyRow], decision: str, execute: bool, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row.copy_status] = by_status.get(row.copy_status, 0) + 1
    lines = [
        "# Approved Migration Copy Status",
        "",
        f"Decision: `{decision}`",
        "",
        "## Safety",
        "",
        f"- Execute mode: `{execute}`",
        "- Only rows with `approved=true` are considered.",
        "- `local_assets/` payloads are rejected.",
        "- No unknown process is killed and no source file is deleted.",
        "",
        "## Counts",
        "",
        f"- Approved rows considered: `{len(rows)}`",
        "",
        "### By Copy Status",
        "",
    ]
    if by_status:
        for key, value in sorted(by_status.items()):
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- none")
    lines.extend(["", "## Next Action", ""])
    if decision == "APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS":
        lines.append("Review `reports/migration/approved_copy_manifest_template.tsv` and explicitly mark only required restore assets as `approved=true` after NAS/data visibility is confirmed.")
    elif decision == "APPROVED_COPY_DRYRUN_READY":
        lines.append("Review dry-run commands and rerun with `--execute` plus `MIGRATION_APPROVED=1 MIGRATION_COPY_APPROVED=1` only when ready.")
    else:
        lines.append("Inspect row-level CSV status before any further migration step.")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(rows: list[ApprovedCopyRow], decision: str, execute: bool, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "decision": decision,
        "execute": execute,
        "approved_rows": len(rows),
        "rows": [asdict(row) for row in rows],
        "safety": {
            "only_approved_true": True,
            "local_assets_rejected": True,
            "deleted_files": False,
        },
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run or dry-run migration copies for explicitly approved rows only")
    ap.add_argument("--copy_plan", default="reports/migration/approved_copy_manifest_template.tsv")
    ap.add_argument("--migration_root", default="/mnt/workspace/hj/nas_hj/world_model_phys_migration_20260708")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--output_csv", default="reports/migration/approved_copy_status.csv")
    ap.add_argument("--output_json", default="reports/migration/approved_copy_status.json")
    ap.add_argument("--summary", default="reports/migration/approved_copy_status_summary.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    migration_root = Path(args.migration_root)
    rows = build_rows(args.copy_plan, migration_root)
    decision = decision_for(rows, migration_root, args.execute)
    should_run = args.execute and decision not in {
        "APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS",
        "APPROVED_COPY_BLOCKED_MIGRATION_APPROVED_ENV",
        "APPROVED_COPY_BLOCKED_COPY_APPROVED_ENV",
        "APPROVED_COPY_BLOCKED_NAS_MISSING",
        "APPROVED_COPY_BLOCKED_ROW_VALIDATION",
    }
    if should_run:
        rows = [run_rsync(row, dry_run=False) for row in rows]
        decision = decision_for(rows, migration_root, args.execute)
    elif rows and not args.execute and not any(row.copy_status.startswith("BLOCKED") for row in rows):
        rows = [run_rsync(row, dry_run=True) for row in rows]
        decision = decision_for(rows, migration_root, args.execute)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.execute, args.output_json)
    write_summary(rows, decision, args.execute, args.summary)
    print(json.dumps({"decision": decision, "approved_rows": len(rows), "execute": args.execute}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
