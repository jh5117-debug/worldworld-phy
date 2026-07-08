from pathlib import Path

from cam_physgeo.data.physeditworld_manifest_init import init_manifest, decision_for


def test_init_manifest_creates_missing_jsonl(tmp_path):
    p = tmp_path / "manifests" / "physeditworld_50h_lingbot_val.jsonl"
    row = init_manifest(p)
    assert row.status == "CREATED"
    assert p.exists()
    assert p.read_text() == ""


def test_init_manifest_keeps_existing_nonempty(tmp_path):
    p = tmp_path / "m.jsonl"
    p.write_text('{"sample_id":"x"}\n', encoding="utf-8")
    row = init_manifest(p)
    assert row.status == "EXISTS"
    assert row.rows == 1
    assert p.read_text(encoding="utf-8") == '{"sample_id":"x"}\n'


def test_decision_for_created():
    row = init_manifest(Path("/tmp/nonexistent-parent-for-unit/skip.jsonl"), dry_run=True)
    assert decision_for([row]) == "PHYS_EDITWORLD_EMPTY_MANIFESTS_DRY_RUN"
