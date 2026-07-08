from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class ManifestRow:
    manifest_kind: str
    row_index: int
    category: str
    path: str
    resolved_target: str
    checked_path: str
    exists: bool
    file_type: str
    size_bytes: int | None
    sha256_status: str
    sha256_expected: str
    sha256_observed: str
    validation_status: str
    copy_recommendation: str
    notes: str


@dataclass
class NasStatus:
    path: str
    exists: bool
    is_dir: bool
    readable: bool
    writable: bool
    free_bytes: int | None
    status: str
    error_reason: str = ""


@dataclass
class GuardStatus:
    path: str
    exists: bool
    has_migration_approved_guard: bool
    has_local_assets_exclusion_note: bool
    status: str


def _boolish(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def read_tsv(path: str | Path) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def sha256_file(path: Path, max_hash_bytes: int) -> tuple[str, str]:
    size = path.stat().st_size
    if size > max_hash_bytes:
        return "SKIPPED_LARGE_FILE", ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "SHA256_OK", h.hexdigest()


def validate_manifest(manifest_kind: str, manifest_path: str | Path, max_hash_bytes: int) -> list[ManifestRow]:
    rows: list[ManifestRow] = []
    for idx, row in enumerate(read_tsv(manifest_path), start=1):
        raw_path = row.get("path", "")
        resolved = row.get("resolved_target", "")
        checked = resolved or raw_path
        p = Path(checked) if checked else Path("__missing_path__")
        file_type = row.get("file_type", "") or ("dir" if p.is_dir() else "file" if p.is_file() else "missing")
        size_value = row.get("size_bytes", "")
        try:
            size_bytes = int(size_value) if size_value not in {"", None} else (p.stat().st_size if p.exists() and p.is_file() else None)
        except OSError:
            size_bytes = None
        expected = row.get("sha256", "")
        manifest_sha_status = row.get("sha256_status", "")
        observed = ""
        sha_status = manifest_sha_status or "NOT_PROVIDED"
        if not checked:
            validation_status = "MISSING_PATH"
        elif not p.exists():
            validation_status = "MISSING_ON_DISK"
        elif p.is_dir():
            validation_status = "DIR_PRESENT_NOT_HASHED"
        elif expected:
            sha_status, observed = sha256_file(p, max_hash_bytes)
            if observed and observed != expected:
                validation_status = "SHA256_MISMATCH"
            elif sha_status == "SKIPPED_LARGE_FILE":
                validation_status = "FILE_PRESENT_SHA256_SKIPPED_LARGE"
            else:
                validation_status = "FILE_PRESENT_SHA256_OK"
        elif p.is_file():
            validation_status = "FILE_PRESENT_NO_SHA256"
        else:
            validation_status = "UNKNOWN"
        rows.append(ManifestRow(
            manifest_kind=manifest_kind,
            row_index=idx,
            category=row.get("category", ""),
            path=raw_path,
            resolved_target=resolved,
            checked_path=str(p),
            exists=p.exists(),
            file_type=file_type,
            size_bytes=size_bytes,
            sha256_status=sha_status,
            sha256_expected=expected,
            sha256_observed=observed,
            validation_status=validation_status,
            copy_recommendation=row.get("copy_recommendation", ""),
            notes=row.get("notes", ""),
        ))
    return rows


def inspect_nas(path: str | Path) -> NasStatus:
    p = Path(path)
    try:
        exists = p.exists()
        is_dir = p.is_dir()
        readable = os.access(p, os.R_OK) if exists else False
        writable = os.access(p, os.W_OK) if exists else False
        free_bytes = None
        if exists:
            st = os.statvfs(p)
            free_bytes = st.f_bavail * st.f_frsize
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
        return NasStatus(str(p), exists, is_dir, readable, writable, free_bytes, status)
    except Exception as exc:
        return NasStatus(str(p), False, False, False, False, None, "BLOCKED_ERROR", repr(exc))


def inspect_execute_guard(path: str | Path) -> GuardStatus:
    p = Path(path)
    if not p.exists():
        return GuardStatus(str(p), False, False, False, "MISSING")
    text = p.read_text(encoding="utf-8", errors="replace")
    has_guard = "MIGRATION_APPROVED" in text and "!= \"1\"" in text
    has_exclusion_note = "local_assets" in text or "not automatic" in text
    status = "PASS" if has_guard else "BLOCKED_NO_APPROVAL_GUARD"
    return GuardStatus(str(p), True, has_guard, has_exclusion_note, status)


def write_csv(rows: Iterable[ManifestRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(ManifestRow.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def summarize_rows(rows: list[ManifestRow]) -> dict[str, object]:
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_file_type: dict[str, int] = {}
    total_file_bytes = 0
    for row in rows:
        by_kind[row.manifest_kind] = by_kind.get(row.manifest_kind, 0) + 1
        by_status[row.validation_status] = by_status.get(row.validation_status, 0) + 1
        by_file_type[row.file_type] = by_file_type.get(row.file_type, 0) + 1
        if row.exists and row.file_type == "file" and row.size_bytes:
            total_file_bytes += row.size_bytes
    return {
        "rows": len(rows),
        "by_kind": by_kind,
        "by_status": by_status,
        "by_file_type": by_file_type,
        "total_present_file_bytes": total_file_bytes,
    }


def overall_decision(rows: list[ManifestRow], nas: NasStatus, guard: GuardStatus) -> str:
    if nas.status != "PASS":
        return "MIGRATION_ASSET_VALIDATION_NAS_BLOCKED"
    if guard.status != "PASS":
        return "MIGRATION_ASSET_VALIDATION_GUARD_BLOCKED"
    if not rows:
        return "MIGRATION_ASSET_VALIDATION_MANIFESTS_MISSING"
    if any(row.validation_status in {"SHA256_MISMATCH", "MISSING_PATH"} for row in rows):
        return "MIGRATION_ASSET_VALIDATION_FAILED"
    if any(row.validation_status == "MISSING_ON_DISK" for row in rows):
        return "MIGRATION_ASSET_VALIDATION_REVIEW_MISSING_CANDIDATES"
    return "MIGRATION_ASSET_VALIDATION_PASS"


def write_json(rows: list[ManifestRow], nas: NasStatus, guard: GuardStatus, decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "decision": decision,
        "summary": summarize_rows(rows),
        "nas": asdict(nas),
        "execute_guard": asdict(guard),
        "safety": {
            "copied_files": False,
            "deleted_files": False,
            "hashed_large_files": False,
            "local_assets_included": False,
        },
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_bytes(value: int | None) -> str:
    if value is None:
        return "unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(value)
    for unit in units:
        if f < 1024 or unit == units[-1]:
            return f"{f:.2f} {unit}"
        f /= 1024
    return str(value)


def write_summary(rows: list[ManifestRow], nas: NasStatus, guard: GuardStatus, decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    summary = summarize_rows(rows)
    lines = [
        "# PhysEditWorld Migration Asset Validation",
        "",
        f"Decision: `{decision}`",
        "",
        "## Safety",
        "",
        "- No files were copied.",
        "- No files, checkpoints, weights, or data were deleted.",
        "- Directories and large files were not recursively hashed.",
        "- `local_assets/` is not included as a migration payload.",
        "",
        "## NAS Target",
        "",
        f"- Path: `{nas.path}`",
        f"- Status: `{nas.status}`",
        f"- Exists/readable/writable: `{nas.exists}` / `{nas.readable}` / `{nas.writable}`",
        f"- Free bytes: `{format_bytes(nas.free_bytes)}`",
        "",
        "## Execute Guard",
        "",
        f"- Path: `{guard.path}`",
        f"- Status: `{guard.status}`",
        f"- Requires `MIGRATION_APPROVED=1`: `{guard.has_migration_approved_guard}`",
        "",
        "## Manifest Summary",
        "",
        f"- Rows: `{summary['rows']}`",
        f"- Present file bytes counted: `{format_bytes(summary['total_present_file_bytes'])}`",
        "",
        "### By Kind",
        "",
    ]
    for key, value in sorted(summary["by_kind"].items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "### By Validation Status", ""])
    for key, value in sorted(summary["by_status"].items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Next Action", ""])
    if decision == "MIGRATION_ASSET_VALIDATION_NAS_BLOCKED":
        lines.append("Mount or expose `/mnt/workspace/hj/nas_hj`, then rerun `bash scripts/migration/validate_physeditworld_migration_assets.sh` before any execute migration.")
    elif decision == "MIGRATION_ASSET_VALIDATION_PASS":
        lines.append("Review candidate manifests, approve the explicit copy list, and only then run the guarded rsync execute script with `MIGRATION_APPROVED=1`.")
    else:
        lines.append("Inspect the CSV rows with non-PASS validation statuses before copying any assets.")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Validate PhysEditWorld migration asset manifests without copying data")
    ap.add_argument("--weights_manifest", default="reports/migration/required_weights_manifest.tsv")
    ap.add_argument("--data_manifest", default="reports/migration/required_data_manifest.tsv")
    ap.add_argument("--nas_root", default="/mnt/workspace/hj/nas_hj")
    ap.add_argument("--execute_script", default="scripts/migration/rsync_h20_to_pai_execute.sh")
    ap.add_argument("--output_csv", default="reports/migration/migration_asset_validation.csv")
    ap.add_argument("--output_json", default="reports/migration/migration_asset_validation.json")
    ap.add_argument("--summary", default="reports/migration/migration_asset_validation_summary.md")
    ap.add_argument("--max_hash_mb", type=int, default=64)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    max_hash_bytes = args.max_hash_mb * 1024 * 1024
    rows = []
    rows.extend(validate_manifest("weights", args.weights_manifest, max_hash_bytes))
    rows.extend(validate_manifest("data", args.data_manifest, max_hash_bytes))
    nas = inspect_nas(args.nas_root)
    guard = inspect_execute_guard(args.execute_script)
    decision = overall_decision(rows, nas, guard)
    write_csv(rows, args.output_csv)
    write_json(rows, nas, guard, decision, args.output_json)
    write_summary(rows, nas, guard, decision, args.summary)
    print(json.dumps({"decision": decision, "rows": len(rows), "nas_status": nas.status, "guard_status": guard.status}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
