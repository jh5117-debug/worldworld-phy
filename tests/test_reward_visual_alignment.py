
from scripts.audit_reward_visual_alignment_v5 import MIN_LOCAL_MEAN, MIN_LOCAL_P95, MIN_VISUAL_SCORE


def test_visual_alignment_gate_is_stricter_than_v4_proxy_reward():
    assert MIN_LOCAL_P95 >= 35.0
    assert MIN_LOCAL_MEAN >= 6.0
    assert MIN_VISUAL_SCORE >= 0.07
