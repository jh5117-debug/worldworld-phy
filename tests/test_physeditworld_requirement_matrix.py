from cam_physgeo.orchestration.physeditworld_requirement_matrix import PHASE0_DECISION_GATES, RequirementRow, overall_decision


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
