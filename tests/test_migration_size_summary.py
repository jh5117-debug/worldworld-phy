from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from cam_physgeo.orchestration.migration_size_summary import build_summary, metric_rows


def _write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def test_migration_size_summary_no_approved_rows(tmp_path: Path) -> None:
    manifest_fields = {
        "category": "model",
        "path": "x",
        "resolved_target": "",
        "exists": "True",
        "file_type": "file",
        "size_bytes": "100",
        "mtime": "",
        "sha256_status": "SHA256_OK",
        "sha256": "abc",
        "copy_recommendation": "REVIEW",
        "notes": "",
    }
    weights = tmp_path / "weights.tsv"
    data = tmp_path / "data.tsv"
    _write_tsv(weights, [manifest_fields])
    _write_tsv(data, [{**manifest_fields, "file_type": "dir", "size_bytes": "4096"}])
    approved = tmp_path / "approved.tsv"
    _write_tsv(approved, [{
        "manifest_kind": "weights",
        "row_index": "1",
        "category": "model",
        "manifest_path": "x",
        "resolved_target": "",
        "copy_source": "x",
        "destination_subdir": "weights",
        "exists": "True",
        "file_type": "file",
        "size_bytes": "100",
        "sha256_status": "SHA256_OK",
        "sha256": "abc",
        "copy_recommendation": "REVIEW",
        "approved": "false",
        "approval_reason": "review required",
        "copy_status": "NEEDS_REVIEW_FILE",
        "notes": "",
    }])
    status = tmp_path / "status.json"
    status.write_text(json.dumps({"decision": "APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS", "approved_rows": 0}), encoding="utf-8")

    summary = build_summary(weights, data, approved, status, tmp_path / "missing_nas")
    assert summary["decision"] == "MIGRATION_SIZE_SUMMARY_NO_APPROVED_ROWS"
    assert summary["candidate_summary"]["manifest_rows"] == 2
    assert summary["candidate_summary"]["present_file_bytes"] == 100
    assert summary["candidate_summary"]["dir_rows_pending_recursive_size"] == 1
    assert summary["approved_copy_summary"]["approved_rows"] == 0
    assert any(row["metric"] == "candidate_present_file_bytes" for row in metric_rows(summary))


def test_migration_size_summary_ready_after_approval(tmp_path: Path) -> None:
    base_row = {
        "category": "model",
        "path": "x",
        "resolved_target": "",
        "exists": "True",
        "file_type": "file",
        "size_bytes": "123",
        "mtime": "",
        "sha256_status": "SHA256_OK",
        "sha256": "abc",
        "copy_recommendation": "REVIEW",
        "notes": "",
    }
    weights = tmp_path / "weights.tsv"
    data = tmp_path / "data.tsv"
    _write_tsv(weights, [base_row])
    _write_tsv(data, [base_row])
    approved = tmp_path / "approved.tsv"
    _write_tsv(approved, [{
        "manifest_kind": "weights",
        "row_index": "1",
        "category": "model",
        "manifest_path": "x",
        "resolved_target": "",
        "copy_source": "x",
        "destination_subdir": "weights",
        "exists": "True",
        "file_type": "file",
        "size_bytes": "123",
        "sha256_status": "SHA256_OK",
        "sha256": "abc",
        "copy_recommendation": "REVIEW",
        "approved": "true",
        "approval_reason": "test",
        "copy_status": "APPROVED_FILE",
        "notes": "",
    }])
    status = tmp_path / "status.json"
    status.write_text(json.dumps({"decision": "APPROVED_COPY_DRYRUN_READY", "approved_rows": 1}), encoding="utf-8")
    nas = tmp_path / "nas"
    nas.mkdir()

    summary = build_summary(weights, data, approved, status, nas)
    assert summary["decision"] == "MIGRATION_SIZE_SUMMARY_READY_FOR_APPROVED_DRYRUN"
    assert summary["approved_copy_summary"]["approved_present_file_bytes"] == 123


if __name__ == "__main__":
    root = Path("/tmp/test_migration_size_summary_direct")
    if root.exists():
        shutil.rmtree(root)
    (root / "a").mkdir(parents=True)
    (root / "b").mkdir(parents=True)
    test_migration_size_summary_no_approved_rows(root / "a")
    test_migration_size_summary_ready_after_approval(root / "b")
