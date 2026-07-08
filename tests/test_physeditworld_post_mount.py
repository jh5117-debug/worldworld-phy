import json

from cam_physgeo.orchestration.physeditworld_post_mount import StepResult, overall, split_roots, validate_root_lock


def test_split_roots_accepts_colon_and_comma():
    assert split_roots("/a:/b,/c") == ["/a", "/b", "/c"]


def test_post_mount_blocks_at_first_bad_step():
    decision = overall([StepResult("root_input", "BLOCKED", "x")])
    assert decision == "POST_MOUNT_BLOCKED_AT_ROOT_INPUT"


def test_post_mount_success_decision():
    decision = overall([StepResult("manifest_audit", "PASS", "x"), StepResult("split", "PASS", "x")])
    assert decision == "POST_MOUNT_PHASE12_DONE_RUN_PIPELINE_GATE_NEXT"


def test_root_lock_missing_blocks(tmp_path):
    row = validate_root_lock([str(tmp_path / "root")], tmp_path / "missing.lock.json")
    assert row.status == "BLOCKED"
    assert row.decision == "POST_MOUNT_BLOCKED_NO_ROOT_LOCK"


def test_root_lock_mismatch_blocks(tmp_path):
    root = tmp_path / "root"
    other = tmp_path / "other"
    lock = tmp_path / "lock.json"
    lock.write_text(json.dumps({
        "decision": "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED",
        "roots": [{"root": str(other), "status": "LOCKED"}],
    }))
    row = validate_root_lock([str(root)], lock)
    assert row.status == "BLOCKED"
    assert row.decision == "POST_MOUNT_BLOCKED_ROOT_LOCK_MISMATCH"


def test_root_lock_passes_for_matching_locked_root(tmp_path):
    root = tmp_path / "root"
    lock = tmp_path / "lock.json"
    lock.write_text(json.dumps({
        "decision": "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED",
        "roots": [{"root": str(root), "status": "LOCKED"}],
    }))
    row = validate_root_lock([str(root)], lock)
    assert row.status == "PASS"
    assert row.decision == "POST_MOUNT_ROOT_LOCK_PASS"
