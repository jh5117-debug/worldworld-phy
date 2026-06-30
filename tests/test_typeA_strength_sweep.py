
from scripts.build_reward_guided_protocol_v4 import SEVERITIES


def test_typea_strength_sweep_has_four_ordered_severities():
    names = [name for name, _ in SEVERITIES]
    strengths = [strength for _, strength in SEVERITIES]
    assert names == ["s1_weak", "s2_medium", "s3_strong", "s4_strong_pass"]
    assert strengths == sorted(strengths)
