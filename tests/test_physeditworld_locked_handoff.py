from cam_physgeo.orchestration.physeditworld_locked_handoff import SequenceStep, overall_decision, status_for_decision


def test_status_for_pass_decision():
    assert status_for_decision("PHYS_EDITWORLD_ROOT_SELECTION_LOCKED", 0) == "PASS"


def test_status_for_blocked_decision():
    assert status_for_decision("POST_MOUNT_BLOCKED_NO_ROOT_LOCK", 0) == "BLOCKED"


def test_status_for_nonzero_exit_fails():
    assert status_for_decision("PHYS_EDITWORLD_ROOT_SELECTION_LOCKED", 2) == "FAIL"


def test_overall_blocks_at_first_bad_step():
    decision = overall_decision([
        SequenceStep("root_selection", "PASS", "cmd", "e", "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED"),
        SequenceStep("post_mount", "BLOCKED", "cmd", "e", "POST_MOUNT_BLOCKED_NO_ROOT_LOCK"),
    ])
    assert decision == "LOCKED_HANDOFF_BLOCKED_AT_POST_MOUNT"


def test_overall_ready_when_all_pass():
    decision = overall_decision([
        SequenceStep("root_selection", "PASS", "cmd", "e", "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED"),
        SequenceStep("post_mount", "PASS", "cmd", "e", "POST_MOUNT_PHASE12_DONE_RUN_PIPELINE_GATE_NEXT"),
    ])
    assert decision == "LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE"
