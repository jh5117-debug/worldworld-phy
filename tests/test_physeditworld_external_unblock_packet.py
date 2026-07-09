from cam_physgeo.orchestration.physeditworld_external_unblock_packet import (
    REQUIRED_ROOT_EVIDENCE,
    DECISION_PATHS,
    derive_decision,
    path_snapshot,
    split_roots,
)


def test_split_roots_accepts_colon_and_comma():
    assert split_roots("/a:/b,/c") == ["/a", "/b", "/c"]


def test_required_root_evidence_keeps_action_camera_gravity_replay():
    evidence = set(REQUIRED_ROOT_EVIDENCE)
    assert "action_trace" in evidence
    assert "camera_trajectory_or_poses" in evidence
    assert "intrinsics" in evidence
    assert "gravity_label_or_metadata" in evidence
    assert "replay_group_or_matched_replay_metadata" in evidence


def test_external_unblock_blocks_missing_nas_or_root():
    decision, blockers = derive_decision(
        path_snapshot("nas", "/definitely/missing/nas"),
        [],
    )
    assert decision == "PHYS_EDITWORLD_EXTERNAL_UNBLOCK_REQUIRED_NAS_OR_ROOT"
    assert "NAS_TARGET_MISSING" in blockers
    assert "PHYS_EDITWORLD_ROOTS_UNSET" in blockers


def test_external_unblock_decision_paths_include_size_summary():
    paths = dict(DECISION_PATHS)
    assert paths["migration_size_summary"] == "reports/migration/migration_size_summary.json"


def test_external_unblock_decision_paths_include_approval_review_packet():
    paths = dict(DECISION_PATHS)
    assert paths["migration_approval_review"] == "reports/migration/migration_approval_review_packet.json"


def test_external_unblock_decision_paths_include_root_submission_template():
    paths = dict(DECISION_PATHS)
    assert paths["root_submission_template"] == "reports/migration/physeditworld_root_submission_template.json"
    assert paths["root_submission_validation"] == "reports/migration/physeditworld_root_submission_validation.json"
    assert paths["root_evidence_samples"] == "reports/migration/physeditworld_root_evidence_samples.json"
