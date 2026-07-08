from pathlib import Path

from cam_physgeo.data.physeditworld_readiness import CheckResult, check_manifest, check_nas_mount, overall_decision


def test_empty_manifest_blocks(tmp_path: Path):
    p = tmp_path / "empty.jsonl"
    p.write_text("")
    out = check_manifest(p, "strict_manifest", require_rows=True)
    assert out.status == "BLOCKED"
    assert out.rows == 0
    assert "zero rows" in out.error_reason


def test_nonempty_manifest_passes(tmp_path: Path):
    p = tmp_path / "rows.jsonl"
    p.write_text('{"sample_id":"s"}\n')
    out = check_manifest(p, "strict_manifest", require_rows=True)
    assert out.status == "PASS"
    assert out.rows == 1


def test_missing_nas_blocks(tmp_path: Path):
    out = check_nas_mount(tmp_path / "missing")
    assert out.status == "BLOCKED"


def test_overall_blocks_on_strict_manifest():
    decision = overall_decision([
        CheckResult("strict_manifest", "BLOCKED"),
        CheckResult("lingbot_train_manifest", "PASS"),
        CheckResult("nas_mount", "PASS"),
    ])
    assert decision == "PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED"
