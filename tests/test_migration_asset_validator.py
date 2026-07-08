from pathlib import Path

from cam_physgeo.orchestration.migration_asset_validator import (
    GuardStatus,
    NasStatus,
    inspect_execute_guard,
    overall_decision,
    validate_manifest,
)


def test_overall_blocks_when_nas_missing():
    decision = overall_decision(
        [],
        NasStatus("/missing", False, False, False, False, None, "BLOCKED_MISSING"),
        GuardStatus("script", True, True, True, "PASS"),
    )
    assert decision == "MIGRATION_ASSET_VALIDATION_NAS_BLOCKED"


def test_execute_guard_detects_migration_approval(tmp_path: Path):
    script = tmp_path / "execute.sh"
    script.write_text('if [[ "${MIGRATION_APPROVED:-0}" != "1" ]]; then exit 2; fi\n', encoding="utf-8")
    guard = inspect_execute_guard(script)
    assert guard.status == "PASS"
    assert guard.has_migration_approved_guard is True


def test_validate_manifest_checks_small_sha(tmp_path: Path):
    payload = tmp_path / "payload.txt"
    payload.write_text("abc", encoding="utf-8")
    import hashlib

    digest = hashlib.sha256(b"abc").hexdigest()
    manifest = tmp_path / "manifest.tsv"
    manifest.write_text(
        "category\tpath\tresolved_target\texists\tfile_type\tsize_bytes\tmtime\tsha256_status\tsha256\tcopy_recommendation\tnotes\n"
        f"test\t{payload}\t\tTrue\tfile\t3\t\tSHA256_OK\t{digest}\tCOPY\tunit\n",
        encoding="utf-8",
    )
    rows = validate_manifest("data", manifest, max_hash_bytes=1024)
    assert len(rows) == 1
    assert rows[0].validation_status == "FILE_PRESENT_SHA256_OK"
    assert rows[0].sha256_observed == digest
