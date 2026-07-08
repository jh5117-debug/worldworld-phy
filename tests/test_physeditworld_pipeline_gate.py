from cam_physgeo.orchestration.physeditworld_pipeline_gate import PhaseStatus, pipeline_decision, read_md_decision, status_for_expected_decision


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


def test_pipeline_blocks_at_backend_readiness_before_baseline():
    decision = pipeline_decision([
        PhaseStatus("readiness", "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT", "PASS", "x"),
        PhaseStatus("asset_validation", "MIGRATION_ASSET_VALIDATION_PASS", "PASS", "y"),
        PhaseStatus("approved_copy", "APPROVED_COPY_DRYRUN_READY", "PASS", "z"),
        PhaseStatus("backend_readiness", "PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY", "BLOCKED", "backend_readiness.json"),
        PhaseStatus("baseline", "BASELINE_READY", "PASS", "summary.md"),
    ])
    assert decision == "PIPELINE_BLOCKED_AT_BACKEND_READINESS"


def test_pipeline_blocks_at_root_schema_before_readiness():
    decision = pipeline_decision([
        PhaseStatus("manifest_init", "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT", "PASS", "x"),
        PhaseStatus("root_schema_probe", "PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT", "BLOCKED", "y"),
        PhaseStatus("readiness", "PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED", "BLOCKED", "z"),
    ])
    assert decision == "PIPELINE_BLOCKED_AT_ROOT_SCHEMA_PROBE"


def test_pipeline_blocks_at_pair_manifest_validation_before_tiny_dpo():
    decision = pipeline_decision([
        PhaseStatus("pair_builder", "READY_FOR_TINY_ANCHORED_DPO", "PASS", "pair_summary.md"),
        PhaseStatus(
            "pair_manifest_validation",
            "PHYS_EDITWORLD_PAIR_MANIFEST_BLOCKED_INSUFFICIENT_READY",
            "BLOCKED",
            "pair_manifest_validation.json",
        ),
        PhaseStatus("tiny_dpo", "TINY_DPO_READY_DRY_RUN", "PASS", "best_checkpoint_decision.json"),
    ])
    assert decision == "PIPELINE_BLOCKED_AT_PAIR_MANIFEST_VALIDATION"


def test_status_for_expected_decision_requires_exact_pass():
    assert status_for_expected_decision("PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT", {"PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"}) == "PASS"
    assert status_for_expected_decision("PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT", {"PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"}) == "BLOCKED"
