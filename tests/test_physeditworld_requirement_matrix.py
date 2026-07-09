from cam_physgeo.orchestration.physeditworld_requirement_matrix import PHASE0_DECISION_GATES, RequirementRow, build_rows, overall_decision


def test_requirement_matrix_blocks_at_migration_readiness():
    decision = overall_decision([
        RequirementRow("0_migration", "PAI/NAS and data readiness", "BLOCKED", "x"),
        RequirementRow("1_data_audit", "strict selected 50h manifest", "BLOCKED", "x"),
    ])
    assert decision == "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS"


def test_requirement_matrix_passes_when_all_pass():
    decision = overall_decision([
        RequirementRow("0_migration", "PAI/NAS and data readiness", "PASS", "x"),
        RequirementRow("1_data_audit", "strict selected 50h manifest", "PASS", "x"),
        RequirementRow("2_conversion", "LingBot train conversion manifest", "PASS", "x"),
        RequirementRow("6_pairs", "anchored DPO pair manifest", "PASS", "x"),
    ])
    assert decision == "PHYS_EDIT_WORLD_PIPELINE_REQUIREMENTS_PASS"

def test_requirement_matrix_blocks_on_asset_validation():
    decision = overall_decision([
        RequirementRow("0_migration", "environment export", "PASS", "x"),
        RequirementRow("0_migration", "migration asset validation", "BLOCKED", "x"),
        RequirementRow("1_data_audit", "strict selected 50h manifest", "PASS", "x"),
    ])
    assert decision == "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS"


def test_phase0_decision_gates_include_locked_root_schema_sequence():
    requirements = {gate[1] for gate in PHASE0_DECISION_GATES}
    assert "expected empty manifest placeholders" in requirements
    assert "selected-root schema probe" in requirements
    assert "locked handoff sequence" in requirements


def test_requirement_matrix_includes_prompt_only_gravity_policy_gate():
    requirements = {row.requirement for row in build_rows()}
    assert "prompt-only gravity policy audit" in requirements


def test_requirement_matrix_includes_pai_bootstrap_restore_entrypoint():
    requirements = {row.requirement for row in build_rows()}
    assert "PAI bootstrap restore entrypoint" in requirements
    assert "PAI bootstrap operator guide" in requirements
    assert "PAI restore-packet wrapper" in requirements
    assert "post-mount continuation wrapper" in requirements
    assert "post-mount continuation operator guide" in requirements
    assert "PAI restore-packet summary" in requirements
    assert "root submission template wrapper" in requirements
    assert "root submission validation wrapper" in requirements
    assert "root evidence sampler wrapper" in requirements
    assert "root onboarding sequence wrapper" in requirements
    assert "external root handoff packet wrapper" in requirements
    assert "external selected-root submission TSV" in requirements
    assert "external selected-root submission guide" in requirements
    assert "external selected-root submission template" in requirements
    assert "external selected-root submission validation" in requirements
    assert "external selected-root evidence samples" in requirements
    assert "external selected-root onboarding sequence" in requirements
    assert "external root handoff packet" in requirements
    assert "PAI restore packet decision" in requirements
    assert "external unblock-packet wrapper" in requirements
    assert "external unblock-packet summary" in requirements
    assert "external unblock packet decision" in requirements


def test_requirement_matrix_includes_downstream_decision_gates():
    requirements = {row.requirement for row in build_rows()}
    assert "baseline true rollout gate" in requirements
    assert "rank32 warm-up preflight" in requirements
    assert "checkpoint video/metric gate" in requirements


def test_requirement_matrix_blocks_at_baseline_before_warmup():
    decision = overall_decision([
        RequirementRow("0_migration", "migration", "PASS", "x"),
        RequirementRow("1_data_audit", "data", "PASS", "x"),
        RequirementRow("2_conversion", "conversion", "PASS", "x"),
        RequirementRow("3_baseline", "baseline true rollout gate", "BLOCKED", "x"),
        RequirementRow("4_warmup", "rank32 warm-up preflight", "BLOCKED", "y"),
    ])
    assert decision == "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_BASELINE"


def test_requirement_matrix_blocks_at_warmup_preflight_after_baseline():
    decision = overall_decision([
        RequirementRow("0_migration", "migration", "PASS", "x"),
        RequirementRow("1_data_audit", "data", "PASS", "x"),
        RequirementRow("2_conversion", "conversion", "PASS", "x"),
        RequirementRow("3_baseline", "baseline true rollout gate", "PASS", "x"),
        RequirementRow("4_warmup", "rank32 warm-up preflight", "BLOCKED", "y"),
    ])
    assert decision == "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_WARMUP_PREFLIGHT"


def test_requirement_matrix_includes_gpu_command_policy_audit():
    requirements = {row.requirement for row in build_rows()}
    assert "PhysEditWorld GPU command policy audit" in requirements


def test_requirement_matrix_includes_git_artifact_policy_audit():
    requirements = {row.requirement for row in build_rows()}
    assert "Git tracked artifact policy audit" in requirements

