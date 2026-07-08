from pathlib import Path

from cam_physgeo.data.physeditworld_prompt_gravity_policy_audit import (
    audit_policy_file,
    audit_prompt_samples,
    decision_for_rows,
    scan_text_for_forbidden,
)


def test_prompt_policy_detects_forbidden_gravity_embedding_text():
    hits = scan_text_for_forbidden("class GravityEmbedding: pass\ngravity_mlp = object()")
    assert hits


def test_prompt_sample_policy_passes():
    rows = audit_prompt_samples()
    assert decision_for_rows(rows) == "PHYS_EDITWORLD_PROMPT_GRAVITY_POLICY_PASS"


def test_policy_file_audit_fails_for_gravity_mlp(tmp_path: Path):
    path = tmp_path / "bad.py"
    path.write_text("gravity_mlp = build()", encoding="utf-8")
    rows = audit_policy_file(path)
    assert decision_for_rows(rows) == "PHYS_EDITWORLD_PROMPT_GRAVITY_POLICY_FAIL"


def test_policy_file_audit_passes_for_prompt_only_config(tmp_path: Path):
    path = tmp_path / "physeditworld_50h_warmup_rank32.yaml"
    path.write_text("condition:\n  gravity: prompt_only\n", encoding="utf-8")
    rows = audit_policy_file(path)
    assert decision_for_rows(rows) == "PHYS_EDITWORLD_PROMPT_GRAVITY_POLICY_PASS"
