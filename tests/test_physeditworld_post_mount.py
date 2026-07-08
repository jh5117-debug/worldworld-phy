import json

from cam_physgeo.orchestration.physeditworld_post_mount import StepResult, main, overall, split_roots, validate_root_lock


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


def test_post_mount_dry_run_keeps_smoke_manifest_noncanonical(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    out_json = tmp_path / "post_mount.json"
    rc = main(
        [
            "--roots",
            str(root),
            "--allow_unlocked_roots",
            "--dry_run",
            "--output_csv",
            str(tmp_path / "post_mount.csv"),
            "--output_json",
            str(out_json),
            "--summary",
            str(tmp_path / "post_mount.md"),
        ]
    )
    assert rc == 0
    payload = json.loads(out_json.read_text(encoding="utf-8"))
    steps = {row["step"]: row for row in payload["steps"]}
    smoke_command = steps["conversion_smoke"]["command"]
    assert "manifests/physeditworld_50h_lingbot_smoke_train.jsonl" in smoke_command
    assert "--manifest_out manifests/physeditworld_50h_lingbot_train.jsonl" not in smoke_command
    assert "conversion_train" not in steps


def test_post_mount_dry_run_full_conversion_adds_canonical_validation(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    out_json = tmp_path / "post_mount.json"
    rc = main(
        [
            "--roots",
            str(root),
            "--allow_unlocked_roots",
            "--dry_run",
            "--run_full_conversion",
            "--output_csv",
            str(tmp_path / "post_mount.csv"),
            "--output_json",
            str(out_json),
            "--summary",
            str(tmp_path / "post_mount.md"),
        ]
    )
    assert rc == 0
    payload = json.loads(out_json.read_text(encoding="utf-8"))
    steps = {row["step"]: row for row in payload["steps"]}
    assert "conversion_train" in steps
    assert "conversion_train_validation" in steps
    assert "manifests/physeditworld_50h_lingbot_train.jsonl" in steps["conversion_train"]["command"]
