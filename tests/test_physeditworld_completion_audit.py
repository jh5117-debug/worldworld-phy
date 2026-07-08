from cam_physgeo.orchestration.physeditworld_completion_audit import (
    AuditRow,
    build_rows,
    overall_decision,
    status_from_decision,
)


def test_status_from_decision_pass():
    assert status_from_decision("WARMUP_GATE_PASS", {"WARMUP_GATE_PASS"}) == "PASS"


def test_status_from_decision_blocked():
    assert status_from_decision("BASELINE_BLOCKED_EMPTY_MANIFEST", {"BASELINE_ROLLOUT_PASS"}) == "BLOCKED"
    assert status_from_decision("PHYS_EDITWORLD_ROOT_INTAKE_WAITING_FOR_EXTERNAL_ROOT", {"PHYS_EDITWORLD_ROOT_INTAKE_LOCKED_READY_FOR_HANDOFF"}) == "BLOCKED"


def test_status_from_decision_missing():
    assert status_from_decision("MISSING", {"X"}) == "MISSING"


def test_overall_blocks_at_earliest_phase():
    rows = [
        AuditRow("phase0_prd", "prd", "PASS", "x"),
        AuditRow("phase0_migration", "root", "BLOCKED", "x"),
        AuditRow("phase1_data", "manifest", "BLOCKED", "y"),
    ]
    assert overall_decision(rows) == "PHYS_EDITWORLD_OBJECTIVE_INCOMPLETE_AT_PHASE0_MIGRATION"


def test_overall_complete_when_all_rows_pass():
    rows = [
        AuditRow("phase0_prd", "prd", "PASS", "x"),
        AuditRow("phase0_migration", "root", "PASS", "x"),
        AuditRow("safety", "forbidden", "PASS", "git"),
    ]
    assert overall_decision(rows) == "PHYS_EDITWORLD_OBJECTIVE_COMPLETE"


def test_build_rows_includes_root_intake_report():
    rows = build_rows()
    requirements = {row.requirement for row in rows}
    assert "expected empty manifest placeholders" in requirements
    assert "selected-root intake handoff report" in requirements
    assert "selected-root schema probe" in requirements


def test_build_rows_includes_pai_bootstrap_restore_entrypoint():
    rows = build_rows()
    requirements = {row.requirement for row in rows}
    assert "PAI bootstrap restore entrypoint" in requirements
    assert "PAI bootstrap operator guide" in requirements
