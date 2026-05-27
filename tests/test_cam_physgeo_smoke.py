from cam_physgeo.data.prompt_templates import build_prompt
from cam_physgeo.data.sample_schema import normalize_sample, validate_sample
from cam_physgeo.dpo.preference_schema import validate_pair
from cam_physgeo.rewards.total_reward import score_sample


def test_prompt_templates():
    assert "synthetic physical scene" in build_prompt(level="P0").lower()
    assert "camera" in build_prompt({"template": "drop", "camera_motion": "reobserve"}, level="P2").lower()


def test_sample_schema_and_reward_stub():
    sample = normalize_sample(
        {"sample_id": "s1", "source": "physion_movingcam", "template": "drop", "camera_motion": "static"}
    )
    assert validate_sample(sample, check_paths=False) == []
    reward = score_sample(sample)
    assert reward["sample_id"] == "s1"
    assert "components" in reward


def test_preference_schema():
    pair = {
        "pair_id": "p1",
        "condition": {},
        "winner": {"video": "a.mp4"},
        "loser": {"video": "b.mp4"},
        "pair_type": "gt_vs_corrupt",
        "margin": 1.0,
        "quality_flags": [],
    }
    assert validate_pair(pair) == []
