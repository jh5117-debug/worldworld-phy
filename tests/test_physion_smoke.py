from cam_physgeo.data.prompt_templates import build_prompt
from cam_physgeo.data.sample_schema import validate_sample, normalize_sample
from cam_physgeo.rewards.total_reward import score_sample


def test_physion_sample_schema_accepts_active_sources():
    sample = normalize_sample(
        {
            "sample_id": "s0",
            "source": "physion_movingcam",
            "template": "collision",
            "camera_motion": "relative_yaw_180_reobserve",
            "has_camera_pose": True,
            "has_intrinsics": True,
        }
    )
    assert validate_sample(sample, check_paths=False) == []


def test_prompt_has_camera_but_no_action():
    prompt = build_prompt({"template": "drop", "camera_motion": "lookaway_reobserve"}, "P2")
    assert "camera" in prompt.lower()
    assert "action" not in prompt.lower()
    assert "trial_complete" not in prompt.lower()


def test_reward_shape_without_video():
    score = score_sample({"sample_id": "s0", "source": "physion_movingcam", "template": "drop"})
    assert 0.0 <= score["reward_total"] <= 1.0
    assert "components" in score
