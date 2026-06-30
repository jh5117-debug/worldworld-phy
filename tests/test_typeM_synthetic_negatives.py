
from scripts.build_reward_guided_protocol_v4 import TYPEM_FAILURES, reward_for_failure, winner_reward
from cam_physgeo.dpo.reward_guided_pair_selector import alignment_decision, compute_total_reward, subreward_margins


def test_typem_failure_modes_cover_rollout_inspired_errors():
    assert "extra_fragment" in TYPEM_FAILURES
    assert "wrong_camera_motion" in TYPEM_FAILURES
    assert "weak_physical_event" in TYPEM_FAILURES


def test_typem_reward_has_positive_aligned_margin():
    winner = winner_reward()
    loser = reward_for_failure("weak_physical_event", 1.1, sharp_ratio=0.9)
    assert compute_total_reward(winner) > compute_total_reward(loser)
    decision = alignment_decision("weak_physical_event", subreward_margins(winner, loser))
    assert decision["aligned"] is True
