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

def test_pipeline_keeps_first_phase_order_for_asset_validation():
    decision = pipeline_decision([
        PhaseStatus("readiness", "PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED", "BLOCKED", "x"),
        PhaseStatus("asset_validation", "MIGRATION_ASSET_VALIDATION_NAS_BLOCKED", "BLOCKED", "y"),
    ])
    assert decision == "PIPELINE_BLOCKED_AT_READINESS"


def test_pipeline_blocks_at_asset_validation_when_readiness_passes():
    decision = pipeline_decision([
        PhaseStatus("readiness", "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT", "PASS", "x"),
        PhaseStatus("asset_validation", "MIGRATION_ASSET_VALIDATION_NAS_BLOCKED", "BLOCKED", "y"),
    ])
    assert decision == "PIPELINE_BLOCKED_AT_ASSET_VALIDATION"

def test_pipeline_blocks_at_approved_copy_when_prior_phase_passes():
    decision = pipeline_decision([
        PhaseStatus("readiness", "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT", "PASS", "x"),
        PhaseStatus("asset_validation", "MIGRATION_ASSET_VALIDATION_PASS", "PASS", "y"),
        PhaseStatus("approved_copy", "APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS", "BLOCKED", "z"),
    ])
    assert decision == "PIPELINE_BLOCKED_AT_APPROVED_COPY"

