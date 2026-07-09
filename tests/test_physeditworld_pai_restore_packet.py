from cam_physgeo.orchestration.physeditworld_pai_restore_packet import (
    READY_BACKEND,
    READY_COMPLETION,
    READY_MATRIX,
    SAFE_NEXT_COMMANDS,
    DECISION_REPORTS,
    decide_restore_packet,
    split_roots,
)


def test_split_roots_accepts_colon_and_comma():
    assert split_roots("/a:/b,/c") == ["/a", "/b", "/c"]


def test_restore_packet_blocks_when_nas_or_root_missing():
    decision, blockers = decide_restore_packet(
        nas_visible=False,
        valid_root_count=0,
        decisions={
            "backend_readiness": READY_BACKEND,
            "requirement_matrix": READY_MATRIX,
            "completion_audit": READY_COMPLETION,
        },
    )
    assert decision == "PAI_RESTORE_PACKET_BLOCKED_NAS_OR_ROOT"
    assert "NAS_TARGET_MISSING" in blockers
    assert "PHYS_EDITWORLD_ROOTS_MISSING_OR_INVALID" in blockers


def test_restore_packet_blocks_when_backend_not_ready():
    decision, blockers = decide_restore_packet(
        nas_visible=True,
        valid_root_count=1,
        decisions={
            "backend_readiness": "PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY",
            "requirement_matrix": READY_MATRIX,
            "completion_audit": READY_COMPLETION,
        },
    )
    assert decision == "PAI_RESTORE_PACKET_BLOCKED_BACKEND_READINESS"
    assert "BACKEND_NOT_READY:PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY" in blockers


def test_restore_packet_safe_next_commands_include_handoff_verifier():
    assert "bash scripts/migration/verify_pai_physeditworld_handoff.sh" in SAFE_NEXT_COMMANDS
    assert "bash scripts/migration/write_physeditworld_external_unblock_packet.sh" in SAFE_NEXT_COMMANDS


def test_restore_packet_decision_reports_include_size_summary():
    reports = dict(DECISION_REPORTS)
    assert reports["migration_size_summary"] == "reports/migration/migration_size_summary.json"


def test_restore_packet_decision_reports_include_approval_review_packet():
    reports = dict(DECISION_REPORTS)
    assert reports["migration_approval_review"] == "reports/migration/migration_approval_review_packet.json"


def test_restore_packet_decision_reports_include_root_submission_template():
    reports = dict(DECISION_REPORTS)
    assert reports["root_submission_template"] == "reports/migration/physeditworld_root_submission_template.json"
    assert reports["root_submission_validation"] == "reports/migration/physeditworld_root_submission_validation.json"
