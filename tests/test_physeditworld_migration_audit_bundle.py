from pathlib import Path

from cam_physgeo.orchestration.physeditworld_migration_audit_bundle import (
    AuditItem,
    CORE_FILES,
    decision_for,
    human_size,
)


def test_human_size_formats_units():
    assert human_size(10) == "10.00B"
    assert human_size(2048) == "2.00KB"
    assert human_size(3 * 1024 * 1024) == "3.00MB"


def test_decision_ready_when_core_files_exist(tmp_path: Path):
    items = []
    for name in CORE_FILES:
        path = tmp_path / name
        path.write_text("x\n", encoding="utf-8")
        items.append(AuditItem(path.stem, str(path), "PASS"))
    assert decision_for(items, tmp_path) == "MIGRATION_AUDIT_BUNDLE_READY"


def test_decision_incomplete_when_core_file_missing(tmp_path: Path):
    items = []
    for name in sorted(CORE_FILES - {"torch_cuda_info.txt"}):
        path = tmp_path / name
        path.write_text("x\n", encoding="utf-8")
        items.append(AuditItem(path.stem, str(path), "PASS"))
    assert decision_for(items, tmp_path) == "MIGRATION_AUDIT_BUNDLE_INCOMPLETE"
