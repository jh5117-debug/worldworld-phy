from cam_physgeo.orchestration.physeditworld_pai_restore_packet import (
    READY_BACKEND,
    READY_COMPLETION,
    READY_MATRIX,
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
