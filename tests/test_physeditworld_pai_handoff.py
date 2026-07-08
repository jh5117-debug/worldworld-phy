from cam_physgeo.orchestration.physeditworld_pai_handoff import (
    EXPECTED_REPORTS,
    REQUIRED_FILES,
    HandoffCheck,
    check_root_input,
    overall_decision,
    split_roots,
)


def test_split_roots_accepts_colon_and_comma():
    roots = split_roots("/a:/b,/c")
    assert roots == ["/a", "/b", "/c"]


def test_missing_root_input_blocks():
    out = check_root_input("")
    assert out.status == "BLOCKED"
    assert "PHYS_EDITWORLD_ROOTS" in out.detail


def test_overall_blocks_on_code_before_nas():
    rows = [
        HandoffCheck("git_branch", "PASS"),
        HandoffCheck("required_handoff_files", "BLOCKED"),
        HandoffCheck("forbidden_staged_files", "PASS"),
        HandoffCheck("phase0_report_artifacts", "PASS"),
        HandoffCheck("nas_target", "PASS"),
        HandoffCheck("physeditworld_root_input", "PASS"),
        HandoffCheck("strict_manifest", "PASS"),
        HandoffCheck("lingbot_train_manifest", "PASS"),
    ]
    assert overall_decision(rows) == "PAI_HANDOFF_BLOCKED_CODE_INCOMPLETE"


def test_overall_blocks_on_nas_or_root_after_code_passes():
    rows = [
        HandoffCheck("git_branch", "PASS"),
        HandoffCheck("required_handoff_files", "PASS"),
        HandoffCheck("forbidden_staged_files", "PASS"),
        HandoffCheck("phase0_report_artifacts", "PASS"),
        HandoffCheck("nas_target", "BLOCKED"),
        HandoffCheck("physeditworld_root_input", "BLOCKED"),
        HandoffCheck("strict_manifest", "BLOCKED"),
        HandoffCheck("lingbot_train_manifest", "BLOCKED"),
    ]
    assert overall_decision(rows) == "PAI_HANDOFF_BLOCKED_NAS_OR_ROOT"


def test_required_files_include_latest_handoff_tools():
    required = set(REQUIRED_FILES)
    assert "scripts/migration/select_physeditworld_root.sh" in required
    assert "scripts/migration/run_physeditworld_locked_handoff_sequence.sh" in required
    assert "scripts/migration/run_physeditworld_completion_audit.sh" in required
    assert "cam_physgeo/orchestration/physeditworld_completion_audit.py" in required


def test_expected_reports_include_root_lock_and_completion_audit():
    expected = set(EXPECTED_REPORTS)
    assert "reports/migration/physeditworld_selected_root_status.json" in expected
    assert "reports/migration/locked_handoff_sequence.json" in expected
    assert "reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json" in expected
