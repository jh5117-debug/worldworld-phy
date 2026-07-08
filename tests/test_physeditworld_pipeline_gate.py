from cam_physgeo.orchestration.physeditworld_pipeline_gate import PhaseStatus, pipeline_decision, read_md_decision


def test_pipeline_blocks_at_first_blocked_phase():
    decision = pipeline_decision([
        PhaseStatus("readiness", "PASS", "PASS", "x"),
        PhaseStatus("baseline", "BASELINE_BLOCKED_EMPTY_MANIFEST", "BLOCKED", "x"),
    ])
    assert decision == "PIPELINE_BLOCKED_AT_BASELINE"


def test_pipeline_ready_when_all_pass():
    decision = pipeline_decision([PhaseStatus("readiness", "PASS", "PASS", "x")])
    assert decision == "PIPELINE_READY_FOR_NEXT_EXECUTION_STEP"


def test_read_md_decision_missing(tmp_path):
    decision, status, error = read_md_decision(tmp_path / "missing.md")
    assert decision == "MISSING"
    assert status == "BLOCKED"
    assert error == "file missing"
