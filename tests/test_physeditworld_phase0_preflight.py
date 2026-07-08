from cam_physgeo.orchestration.physeditworld_phase0_preflight import PreflightStep, overall_decision, status_for


def test_phase0_blocks_at_readiness_first():
    rows = [
        PreflightStep("empty_manifest_init", "cmd", 0, "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT", "PASS", "init"),
        PreflightStep("migration_audit_bundle", "cmd", 0, "MIGRATION_AUDIT_BUNDLE_READY", "PASS", "audit"),
        PreflightStep("physeditworld_root_candidates_ranked", "cmd", 0, "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG", "PASS", "root_candidates"),
        PreflightStep("physeditworld_root_schema_probe", "cmd", 0, "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT", "PASS", "schema"),
        PreflightStep("physeditworld_selected_root_status", "cmd", 0, "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED", "PASS", "root"),
        PreflightStep("physeditworld_root_intake", "cmd", 0, "PHYS_EDITWORLD_ROOT_INTAKE_LOCKED_READY_FOR_HANDOFF", "PASS", "intake"),
        PreflightStep("locked_handoff_sequence", "cmd", 0, "LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE", "PASS", "handoff"),
        PreflightStep("physeditworld_pai_readiness", "cmd", 0, "PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED", "BLOCKED", "x"),
        PreflightStep("migration_asset_validation", "cmd", 0, "MIGRATION_ASSET_VALIDATION_NAS_BLOCKED", "BLOCKED", "y"),
    ]
    assert overall_decision(rows) == "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_READINESS"


def test_phase0_blocks_at_approved_copy_after_prior_passes():
    rows = [
        PreflightStep("empty_manifest_init", "cmd", 0, "PHYS_EDITWORLD_EMPTY_MANIFESTS_INITIALIZED", "PASS", "init"),
        PreflightStep("migration_audit_bundle", "cmd", 0, "MIGRATION_AUDIT_BUNDLE_READY", "PASS", "audit"),
        PreflightStep("physeditworld_root_candidates_ranked", "cmd", 0, "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG", "PASS", "root_candidates"),
        PreflightStep("physeditworld_root_schema_probe", "cmd", 0, "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT", "PASS", "schema"),
        PreflightStep("physeditworld_selected_root_status", "cmd", 0, "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED", "PASS", "root"),
        PreflightStep("physeditworld_root_intake", "cmd", 0, "PHYS_EDITWORLD_ROOT_INTAKE_LOCKED_READY_FOR_HANDOFF", "PASS", "intake"),
        PreflightStep("locked_handoff_sequence", "cmd", 0, "LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE", "PASS", "handoff"),
        PreflightStep("physeditworld_pai_readiness", "cmd", 0, "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT", "PASS", "x"),
        PreflightStep("migration_asset_validation", "cmd", 0, "MIGRATION_ASSET_VALIDATION_PASS", "PASS", "y"),
        PreflightStep("approved_copy_manifest_template", "cmd", 0, "COPY_PLAN_REVIEW_REQUIRED", "REVIEW_REQUIRED", "z"),
        PreflightStep("approved_copy_status", "cmd", 0, "APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS", "BLOCKED", "w"),
    ]
    assert overall_decision(rows) == "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_APPROVED_COPY"


def test_status_for_review_required():
    assert status_for("COPY_PLAN_REVIEW_REQUIRED", 0) == "REVIEW_REQUIRED"


def test_status_for_manifest_init_pass():
    assert status_for("PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT", 0) == "PASS"
    assert status_for("MIGRATION_AUDIT_BUNDLE_READY", 0) == "PASS"


def test_status_for_waiting_is_blocked():
    assert status_for("PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT", 0) == "BLOCKED"
    assert status_for("PHYS_EDITWORLD_ROOT_INTAKE_WAITING_FOR_EXTERNAL_ROOT", 0) == "BLOCKED"
    assert status_for("PHYS_EDITWORLD_EXTERNAL_UNBLOCK_REQUIRED_NAS_OR_ROOT", 0) == "BLOCKED"


def test_phase0_blocks_at_root_schema_before_readiness():
    rows = [
        PreflightStep("empty_manifest_init", "cmd", 0, "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT", "PASS", "init"),
        PreflightStep("migration_audit_bundle", "cmd", 0, "MIGRATION_AUDIT_BUNDLE_READY", "PASS", "audit"),
        PreflightStep("physeditworld_root_candidates_ranked", "cmd", 0, "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG", "PASS", "root_candidates"),
        PreflightStep("physeditworld_root_schema_probe", "cmd", 0, "PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT", "BLOCKED", "schema"),
        PreflightStep("physeditworld_pai_readiness", "cmd", 0, "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT", "PASS", "readiness"),
    ]
    assert overall_decision(rows) == "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_ROOT_SCHEMA_PROBE"


def test_phase0_accepts_locked_handoff_and_pai_handoff_pass_decisions():
    assert status_for("PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT", 0) == "PASS"
    assert status_for("PHYS_EDITWORLD_ROOT_INTAKE_LOCKED_READY_FOR_HANDOFF", 0) == "PASS"
    assert status_for("LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE", 0) == "PASS"
    assert status_for("PAI_HANDOFF_READY_FOR_POST_MOUNT_CONTINUE", 0) == "PASS"
    assert status_for("PHYS_EDITWORLD_BACKEND_READY_FOR_BASELINE_WARMUP", 0) == "PASS"
    assert status_for("PHYS_EDITWORLD_EXTERNAL_UNBLOCK_PACKET_READY_FOR_POST_MOUNT", 0) == "PASS"


def test_phase0_blocks_at_backend_readiness_after_handoff():
    rows = [
        PreflightStep("empty_manifest_init", "cmd", 0, "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT", "PASS", "init"),
        PreflightStep("migration_audit_bundle", "cmd", 0, "MIGRATION_AUDIT_BUNDLE_READY", "PASS", "audit"),
        PreflightStep("physeditworld_root_candidates_ranked", "cmd", 0, "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG", "PASS", "root_candidates"),
        PreflightStep("physeditworld_root_schema_probe", "cmd", 0, "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT", "PASS", "schema"),
        PreflightStep("physeditworld_selected_root_status", "cmd", 0, "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED", "PASS", "root"),
        PreflightStep("physeditworld_root_intake", "cmd", 0, "PHYS_EDITWORLD_ROOT_INTAKE_LOCKED_READY_FOR_HANDOFF", "PASS", "intake"),
        PreflightStep("locked_handoff_sequence", "cmd", 0, "LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE", "PASS", "handoff"),
        PreflightStep("physeditworld_pai_readiness", "cmd", 0, "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT", "PASS", "readiness"),
        PreflightStep("migration_asset_validation", "cmd", 0, "MIGRATION_ASSET_VALIDATION_PASS", "PASS", "asset"),
        PreflightStep("approved_copy_manifest_template", "cmd", 0, "COPY_PLAN_REVIEW_REQUIRED", "REVIEW_REQUIRED", "copy_plan"),
        PreflightStep("approved_copy_status", "cmd", 0, "APPROVED_COPY_DRYRUN_READY", "PASS", "copy"),
        PreflightStep("pai_handoff_status", "cmd", 0, "PAI_HANDOFF_READY_FOR_POST_MOUNT_CONTINUE", "PASS", "handoff"),
        PreflightStep("backend_readiness", "cmd", 0, "PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY", "BLOCKED", "backend"),
    ]
    assert overall_decision(rows) == "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_BACKEND_READINESS"

def test_phase0_blocks_at_external_unblock_packet_after_pipeline_gate():
    rows = [
        PreflightStep("empty_manifest_init", "cmd", 0, "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT", "PASS", "init"),
        PreflightStep("migration_audit_bundle", "cmd", 0, "MIGRATION_AUDIT_BUNDLE_READY", "PASS", "audit"),
        PreflightStep("physeditworld_root_candidates_ranked", "cmd", 0, "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG", "PASS", "root_candidates"),
        PreflightStep("physeditworld_root_schema_probe", "cmd", 0, "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT", "PASS", "schema"),
        PreflightStep("physeditworld_selected_root_status", "cmd", 0, "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED", "PASS", "root"),
        PreflightStep("physeditworld_root_intake", "cmd", 0, "PHYS_EDITWORLD_ROOT_INTAKE_LOCKED_READY_FOR_HANDOFF", "PASS", "intake"),
        PreflightStep("locked_handoff_sequence", "cmd", 0, "LOCKED_HANDOFF_PHASE12_READY_FOR_BASELINE_GATE", "PASS", "handoff"),
        PreflightStep("physeditworld_pai_readiness", "cmd", 0, "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT", "PASS", "readiness"),
        PreflightStep("migration_asset_validation", "cmd", 0, "MIGRATION_ASSET_VALIDATION_PASS", "PASS", "asset"),
        PreflightStep("approved_copy_manifest_template", "cmd", 0, "COPY_PLAN_REVIEW_REQUIRED", "REVIEW_REQUIRED", "copy_plan"),
        PreflightStep("approved_copy_status", "cmd", 0, "APPROVED_COPY_DRYRUN_READY", "PASS", "copy"),
        PreflightStep("pai_handoff_status", "cmd", 0, "PAI_HANDOFF_READY_FOR_POST_MOUNT_CONTINUE", "PASS", "handoff"),
        PreflightStep("backend_readiness", "cmd", 0, "PHYS_EDITWORLD_BACKEND_READY_FOR_BASELINE_WARMUP", "PASS", "backend"),
        PreflightStep("requirement_matrix", "cmd", 0, "PHYS_EDIT_WORLD_PIPELINE_REQUIREMENTS_PASS", "PASS", "matrix"),
        PreflightStep("pipeline_gate_status", "cmd", 0, "PIPELINE_READY_FOR_NEXT_EXECUTION_STEP", "PASS", "pipeline"),
        PreflightStep("physeditworld_external_unblock_packet", "cmd", 0, "PHYS_EDITWORLD_EXTERNAL_UNBLOCK_REQUIRED_NAS_OR_ROOT", "BLOCKED", "external"),
    ]
    assert overall_decision(rows) == "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_EXTERNAL_UNBLOCK_PACKET"

def test_phase0_blocks_at_migration_audit_after_manifest_init():
    rows = [
        PreflightStep("empty_manifest_init", "cmd", 0, "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT", "PASS", "init"),
        PreflightStep("migration_audit_bundle", "cmd", 0, "MIGRATION_AUDIT_BUNDLE_INCOMPLETE", "BLOCKED", "audit"),
        PreflightStep("physeditworld_root_candidates_ranked", "cmd", 0, "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG", "PASS", "root_candidates"),
    ]
    assert overall_decision(rows) == "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_MIGRATION_AUDIT"
