from cam_physgeo.orchestration.physeditworld_post_mount import StepResult, overall, split_roots


def test_split_roots_accepts_colon_and_comma():
    assert split_roots("/a:/b,/c") == ["/a", "/b", "/c"]


def test_post_mount_blocks_at_first_bad_step():
    decision = overall([StepResult("root_input", "BLOCKED", "x")])
    assert decision == "POST_MOUNT_BLOCKED_AT_ROOT_INPUT"


def test_post_mount_success_decision():
    decision = overall([StepResult("manifest_audit", "PASS", "x"), StepResult("split", "PASS", "x")])
    assert decision == "POST_MOUNT_PHASE12_DONE_RUN_PIPELINE_GATE_NEXT"
