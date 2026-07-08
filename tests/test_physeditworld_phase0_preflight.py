from cam_physgeo.orchestration.physeditworld_phase0_preflight import PreflightStep, overall_decision, status_for


def test_phase0_blocks_at_readiness_first():
    rows = [
        PreflightStep("physeditworld_pai_readiness", "cmd", 0, "PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED", "BLOCKED", "x"),
        PreflightStep("migration_asset_validation", "cmd", 0, "MIGRATION_ASSET_VALIDATION_NAS_BLOCKED", "BLOCKED", "y"),
    ]
    assert overall_decision(rows) == "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_READINESS"


def test_phase0_blocks_at_approved_copy_after_prior_passes():
    rows = [
        PreflightStep("physeditworld_pai_readiness", "cmd", 0, "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT", "PASS", "x"),
        PreflightStep("migration_asset_validation", "cmd", 0, "MIGRATION_ASSET_VALIDATION_PASS", "PASS", "y"),
        PreflightStep("approved_copy_manifest_template", "cmd", 0, "COPY_PLAN_REVIEW_REQUIRED", "REVIEW_REQUIRED", "z"),
        PreflightStep("approved_copy_status", "cmd", 0, "APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS", "BLOCKED", "w"),
    ]
    assert overall_decision(rows) == "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_APPROVED_COPY"


def test_status_for_review_required():
    assert status_for("COPY_PLAN_REVIEW_REQUIRED", 0) == "REVIEW_REQUIRED"
