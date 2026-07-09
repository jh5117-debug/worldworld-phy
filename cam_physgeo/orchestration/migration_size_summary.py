from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class ManifestAggregate:
    manifest_kind: str
    manifest_path: str
    rows: int
    exists_true_rows: int
    missing_rows: int
    present_file_rows: int
    present_dir_rows: int
    present_file_bytes: int
    dir_rows_pending_recursive_size: int
    by_file_type: dict[str, int]
    by_sha256_status: dict[str, int]
    by_copy_recommendation: dict[str, int]


@dataclass
class ApprovedCopyAggregate:
    manifest_path: str
    rows: int
    approved_rows: int
    approved_present_file_rows: int
    approved_present_file_bytes: int
    approved_dir_rows_pending_recursive_size: int
    approved_missing_rows: int
    by_copy_status: dict[str, int]
    by_manifest_kind: dict[str, int]


@dataclass
class NasSummary:
    path: str
    exists: bool
    is_dir: bool
    readable: bool
    writable: bool
    free_bytes: int | None
    status: str


def _boolish(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int_or_zero(value: object) -> int:
    try:
        if value in {None, ""}:
            return 0
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def read_tsv(path: str | Path) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _bump(counter: dict[str, int], key: str) -> None:
    key = key or "EMPTY"
    counter[key] = counter.get(key, 0) + 1


def aggregate_manifest(manifest_kind: str, manifest_path: str | Path) -> ManifestAggregate:
    rows = read_tsv(manifest_path)
    by_file_type: dict[str, int] = {}
    by_sha256_status: dict[str, int] = {}
    by_copy_recommendation: dict[str, int] = {}
    exists_true_rows = 0
    missing_rows = 0
    present_file_rows = 0
    present_dir_rows = 0
    present_file_bytes = 0
    for row in rows:
        exists = _boolish(row.get("exists"))
        file_type = row.get("file_type", "") or "unknown"
        _bump(by_file_type, file_type)
        _bump(by_sha256_status, row.get("sha256_status", ""))
        _bump(by_copy_recommendation, row.get("copy_recommendation", ""))
        if exists:
            exists_true_rows += 1
            if file_type == "file":
                present_file_rows += 1
                present_file_bytes += _int_or_zero(row.get("size_bytes"))
            elif file_type == "dir":
                present_dir_rows += 1
        else:
            missing_rows += 1
    return ManifestAggregate(
        manifest_kind=manifest_kind,
        manifest_path=str(manifest_path),
        rows=len(rows),
        exists_true_rows=exists_true_rows,
        missing_rows=missing_rows,
        present_file_rows=present_file_rows,
        present_dir_rows=present_dir_rows,
        present_file_bytes=present_file_bytes,
        dir_rows_pending_recursive_size=present_dir_rows,
        by_file_type=by_file_type,
        by_sha256_status=by_sha256_status,
        by_copy_recommendation=by_copy_recommendation,
    )


def aggregate_approved_copy_template(path: str | Path) -> ApprovedCopyAggregate:
    rows = read_tsv(path)
    by_copy_status: dict[str, int] = {}
    by_manifest_kind: dict[str, int] = {}
    approved_rows = 0
    approved_present_file_rows = 0
    approved_present_file_bytes = 0
    approved_dir_rows_pending_recursive_size = 0
    approved_missing_rows = 0
    for row in rows:
        _bump(by_copy_status, row.get("copy_status", ""))
        _bump(by_manifest_kind, row.get("manifest_kind", ""))
        if not _boolish(row.get("approved")):
            continue
        approved_rows += 1
        exists = _boolish(row.get("exists"))
        file_type = row.get("file_type", "")
        if not exists:
            approved_missing_rows += 1
        elif file_type == "file":
            approved_present_file_rows += 1
            approved_present_file_bytes += _int_or_zero(row.get("size_bytes"))
        elif file_type == "dir":
            approved_dir_rows_pending_recursive_size += 1
    return ApprovedCopyAggregate(
        manifest_path=str(path),
        rows=len(rows),
        approved_rows=approved_rows,
        approved_present_file_rows=approved_present_file_rows,
        approved_present_file_bytes=approved_present_file_bytes,
        approved_dir_rows_pending_recursive_size=approved_dir_rows_pending_recursive_size,
        approved_missing_rows=approved_missing_rows,
        by_copy_status=by_copy_status,
        by_manifest_kind=by_manifest_kind,
    )


def inspect_nas(path: str | Path) -> NasSummary:
    p = Path(path)
    exists = p.exists()
    is_dir = p.is_dir()
    readable = os.access(p, os.R_OK) if exists else False
    writable = os.access(p, os.W_OK) if exists else False
    free_bytes: int | None = None
    if exists:
        try:
            st = os.statvfs(p)
            free_bytes = st.f_bavail * st.f_frsize
        except OSError:
            free_bytes = None
    if not exists:
        status = "BLOCKED_MISSING"
    elif not is_dir:
        status = "BLOCKED_NOT_DIR"
    elif not readable:
        status = "BLOCKED_NOT_READABLE"
    elif not writable:
        status = "BLOCKED_NOT_WRITABLE"
    else:
        status = "PASS"
    return NasSummary(str(p), exists, is_dir, readable, writable, free_bytes, status)


def read_approved_copy_status(path: str | Path) -> dict[str, object]:
    p = Path(path)
    if not p.exists():
        return {"decision": "MISSING", "approved_rows": 0}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"decision": "UNREADABLE", "approved_rows": 0, "error_reason": repr(exc)}
    if not isinstance(data, dict):
        return {"decision": "UNEXPECTED_JSON", "approved_rows": 0}
    return data


def format_bytes(value: int | None) -> str:
    if value is None:
        return "unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    amount = float(value)
    for unit in units:
        if amount < 1024.0 or unit == units[-1]:
            return f"{amount:.2f} {unit}"
        amount /= 1024.0
    return str(value)


def decide(
    manifests: list[ManifestAggregate],
    approved: ApprovedCopyAggregate,
    approved_status: dict[str, object],
    nas: NasSummary,
) -> str:
    if not any(item.rows for item in manifests):
        return "MIGRATION_SIZE_SUMMARY_MANIFESTS_MISSING"
    status_approved_rows = _int_or_zero(approved_status.get("approved_rows"))
    if approved.approved_rows == 0 and status_approved_rows == 0:
        return "MIGRATION_SIZE_SUMMARY_NO_APPROVED_ROWS"
    if nas.status != "PASS":
        return "MIGRATION_SIZE_SUMMARY_NAS_BLOCKED"
    if approved.approved_missing_rows:
        return "MIGRATION_SIZE_SUMMARY_APPROVED_SOURCE_MISSING"
    return "MIGRATION_SIZE_SUMMARY_READY_FOR_APPROVED_DRYRUN"


def build_summary(
    weights_manifest: str | Path,
    data_manifest: str | Path,
    approved_template: str | Path,
    approved_status_path: str | Path,
    nas_path: str | Path,
) -> dict[str, object]:
    manifests = [
        aggregate_manifest("weights", weights_manifest),
        aggregate_manifest("data", data_manifest),
    ]
    approved = aggregate_approved_copy_template(approved_template)
    approved_status = read_approved_copy_status(approved_status_path)
    nas = inspect_nas(nas_path)
    total_present_file_bytes = sum(item.present_file_bytes for item in manifests)
    total_dir_rows_pending = sum(item.dir_rows_pending_recursive_size for item in manifests)
    decision = decide(manifests, approved, approved_status, nas)
    return {
        "decision": decision,
        "candidate_summary": {
            "manifest_rows": sum(item.rows for item in manifests),
            "present_file_bytes": total_present_file_bytes,
            "present_file_bytes_human": format_bytes(total_present_file_bytes),
            "dir_rows_pending_recursive_size": total_dir_rows_pending,
            "missing_rows": sum(item.missing_rows for item in manifests),
        },
        "approved_copy_summary": asdict(approved),
        "approved_copy_status": {
            "path": str(approved_status_path),
            "decision": approved_status.get("decision", "UNKNOWN"),
            "approved_rows": approved_status.get("approved_rows", 0),
            "execute": approved_status.get("execute", False),
        },
        "manifests": [asdict(item) for item in manifests],
        "nas": asdict(nas),
        "safety": {
            "copied_files": False,
            "deleted_files": False,
            "recursive_du_performed": False,
            "local_assets_included_by_policy": False,
        },
    }


def metric_rows(summary: dict[str, object]) -> list[dict[str, str]]:
    candidate = summary["candidate_summary"]  # type: ignore[index]
    approved = summary["approved_copy_summary"]  # type: ignore[index]
    nas = summary["nas"]  # type: ignore[index]
    status = summary["approved_copy_status"]  # type: ignore[index]
    return [
        {"metric": "decision", "value": str(summary["decision"]), "bytes": "", "human": ""},
        {"metric": "candidate_manifest_rows", "value": str(candidate["manifest_rows"]), "bytes": "", "human": ""},
        {"metric": "candidate_present_file_bytes", "value": str(candidate["present_file_bytes"]), "bytes": str(candidate["present_file_bytes"]), "human": str(candidate["present_file_bytes_human"])},
        {"metric": "candidate_dir_rows_pending_recursive_size", "value": str(candidate["dir_rows_pending_recursive_size"]), "bytes": "", "human": ""},
        {"metric": "candidate_missing_rows", "value": str(candidate["missing_rows"]), "bytes": "", "human": ""},
        {"metric": "approved_rows", "value": str(approved["approved_rows"]), "bytes": "", "human": ""},
        {"metric": "approved_present_file_bytes", "value": str(approved["approved_present_file_bytes"]), "bytes": str(approved["approved_present_file_bytes"]), "human": format_bytes(int(approved["approved_present_file_bytes"]))},
        {"metric": "approved_dir_rows_pending_recursive_size", "value": str(approved["approved_dir_rows_pending_recursive_size"]), "bytes": "", "human": ""},
        {"metric": "approved_missing_rows", "value": str(approved["approved_missing_rows"]), "bytes": "", "human": ""},
        {"metric": "approved_copy_status_decision", "value": str(status["decision"]), "bytes": "", "human": ""},
        {"metric": "nas_status", "value": str(nas["status"]), "bytes": "", "human": ""},
        {"metric": "nas_free_bytes", "value": str(nas["free_bytes"]), "bytes": str(nas["free_bytes"] or ""), "human": format_bytes(nas["free_bytes"])},
    ]


def write_csv(rows: Iterable[dict[str, str]], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["metric", "value", "bytes", "human"]
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(summary: dict[str, object], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(summary: dict[str, object], path: str | Path) -> None:
    candidate = summary["candidate_summary"]  # type: ignore[index]
    approved = summary["approved_copy_summary"]  # type: ignore[index]
    status = summary["approved_copy_status"]  # type: ignore[index]
    nas = summary["nas"]  # type: ignore[index]
    manifests = summary["manifests"]  # type: ignore[index]
    lines = [
        "# Migration Size Summary",
        "",
        f"Decision: `{summary['decision']}`",
        "",
        "## Candidate Required Assets",
        "",
        f"- Manifest rows: `{candidate['manifest_rows']}`",
        f"- Present file bytes counted: `{candidate['present_file_bytes']}` ({candidate['present_file_bytes_human']})",
        f"- Directory rows pending recursive sizing: `{candidate['dir_rows_pending_recursive_size']}`",
        f"- Missing rows: `{candidate['missing_rows']}`",
        "",
        "This report intentionally does not run recursive `du` and does not copy or delete any file. Directory rows remain pending until an approved migration payload is selected.",
        "",
        "## Approved Copy Payload",
        "",
        f"- Approved-copy status decision: `{status['decision']}`",
        f"- Approved rows: `{approved['approved_rows']}`",
        f"- Approved present file bytes: `{approved['approved_present_file_bytes']}` ({format_bytes(int(approved['approved_present_file_bytes']))})",
        f"- Approved directory rows pending recursive sizing: `{approved['approved_dir_rows_pending_recursive_size']}`",
        f"- Approved missing rows: `{approved['approved_missing_rows']}`",
        "",
        "## NAS Target",
        "",
        f"- Path: `{nas['path']}`",
        f"- Status: `{nas['status']}`",
        f"- Exists: `{nas['exists']}`; is_dir: `{nas['is_dir']}`; readable: `{nas['readable']}`; writable: `{nas['writable']}`",
        f"- Free bytes: `{nas['free_bytes']}` ({format_bytes(nas['free_bytes'])})",
        "",
        "## Manifest Breakdown",
        "",
        "| kind | rows | present files | present dirs | missing | present file bytes |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in manifests:
        lines.append(
            "| {manifest_kind} | {rows} | {present_file_rows} | {present_dir_rows} | {missing_rows} | {present_file_bytes} |".format(**item)
        )
    lines.extend([
        "",
        "## Safety",
        "",
        "- Copied files: `False`",
        "- Deleted files: `False`",
        "- Recursive directory sizing: `False`",
        "- local_assets included by policy: `False`",
    ])
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize migration candidate and approved payload sizes without copying data.")
    parser.add_argument("--weights_manifest", default="reports/migration/required_weights_manifest.tsv")
    parser.add_argument("--data_manifest", default="reports/migration/required_data_manifest.tsv")
    parser.add_argument("--approved_template", default="reports/migration/approved_copy_manifest_template.tsv")
    parser.add_argument("--approved_status", default="reports/migration/approved_copy_status.json")
    parser.add_argument("--nas_path", default="/mnt/workspace/hj/nas_hj")
    parser.add_argument("--csv_out", default="reports/migration/migration_size_summary.csv")
    parser.add_argument("--json_out", default="reports/migration/migration_size_summary.json")
    parser.add_argument("--md_out", default="reports/migration/migration_size_summary.md")
    args = parser.parse_args()
    summary = build_summary(
        args.weights_manifest,
        args.data_manifest,
        args.approved_template,
        args.approved_status,
        args.nas_path,
    )
    write_csv(metric_rows(summary), args.csv_out)
    write_json(summary, args.json_out)
    write_markdown(summary, args.md_out)
    print(json.dumps({"decision": summary["decision"], "json_out": args.json_out, "md_out": args.md_out}, sort_keys=True))


if __name__ == "__main__":
    main()
