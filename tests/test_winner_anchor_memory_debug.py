from __future__ import annotations

from cam_physgeo.dpo.winner_anchor_memory_debug import STAGES
from cam_physgeo.dpo.winner_anchor_only_runner import is_reviewed_dpo_pair, window_sequence


def test_reviewed_pair_gate_requires_review_and_ready() -> None:
    assert is_reviewed_dpo_pair({"codex_visual_audit": {"reviewed": True, "is_dpo_ready": True}})
    assert not is_reviewed_dpo_pair({"codex_visual_audit": {"reviewed": False, "is_dpo_ready": True}})
    assert not is_reviewed_dpo_pair({"codex_visual_audit": {"reviewed": True, "is_dpo_ready": False}})


def test_window_sequence_falls_back_in_order() -> None:
    assert window_sequence() == [81, 49, 33, 25]
    assert window_sequence(49) == [49, 33, 25]
    assert window_sequence(40) == [40, 33, 25]


def test_memory_audit_stage_names_are_complete() -> None:
    assert STAGES[0] == "0_initial"
    assert "7_policy_forward_grad" in STAGES
    assert STAGES[-1] == "11_after_empty_cache"
