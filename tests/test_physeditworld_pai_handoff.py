from cam_physgeo.orchestration.physeditworld_pai_handoff import HandoffCheck, check_root_input, overall_decision, split_roots


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
