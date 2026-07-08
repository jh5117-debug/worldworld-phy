from cam_physgeo.orchestration.physeditworld_locked_handoff import STEP_SPECS, SequenceStep, overall_decision, status_for_decision


def test_status_for_pass_decision():
    assert status_for_decision("PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT", 0) == "PASS"
    assert status_for_decision("PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT", 0) == "PASS"
    assert status_for_decision("PHYS_EDITWORLD_ROOT_SELECTION_LOCKED", 0) == "PASS"


def test_status_for_blocked_decision():
    assert status_for_decision("PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT", 0) == "BLOCKED"
    assert status_for_decision("POST_MOUNT_BLOCKED_NO_ROOT_LOCK", 0) == "BLOCKED"


def test_status_for_nonzero_exit_fails():
    assert status_for_decision("PHYS_EDITWORLD_ROOT_SELECTION_LOCKED", 2) == "FAIL"


def test_overall_blocks_at_first_bad_step():
    decision = overall_decision([
        SequenceStep("empty_manifest_init", "PASS", "cmd", "e", "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT"),
        SequenceStep("root_schema_probe", "PASS", "cmd", "e", "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"),
        SequenceStep("root_selection", "PASS", "cmd", "e", "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED"),
        SequenceStep("post_mount", "BLOCKED", "cmd", "e", "POST_MOUNT_BLOCKED_NO_ROOT_LOCK"),
    ])
    assert decision == "LOCKED_HANDOFF_BLOCKED_AT_POST_MOUNT"


def test_overall_ready_when_all_pass():
    decision = overall_decision([
        SequenceStep("empty_manifest_init", "PASS", "cmd", "e", "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT"),
        SequenceStep("root_schema_probe", "PASS", "cmd", "e", "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"),
        SequenceStep("root_selection", "PASS", "cmd", "e", "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED"),
        SequenceStep("post_mount", "PASS", "cmd", "e", "POST_MOUNT_PHASE12_DONE_RUN_PIPELINE_GATE_NEXT"),
    ])
    assert decision == "LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE"


def test_locked_handoff_runs_manifest_init_first():
    first = STEP_SPECS[0]
    assert first[0] == "empty_manifest_init"
    assert any("init_physeditworld_empty_manifests.sh" in part for part in first[1])


def test_locked_handoff_runs_schema_probe_before_root_selection():
    names = [spec[0] for spec in STEP_SPECS]
    assert names.index("root_schema_probe") < names.index("root_selection")
    schema_spec = STEP_SPECS[names.index("root_schema_probe")]
    assert any("probe_physeditworld_root_schema.sh" in part for part in schema_spec[1])
