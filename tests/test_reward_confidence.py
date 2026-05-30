from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cam_physgeo.rewards.total_reward import score_sample


def test_missing_video_reward_is_low_confidence():
    sample = {
        "sample_id": "missing",
        "source": "physion_movingcam",
        "template": "drop",
        "camera_motion": "orbit",
        "video_path": "/tmp/does-not-exist.mp4",
        "candidate_video_path": "/tmp/does-not-exist.mp4",
        "poses_path": "/tmp/does-not-exist.npy",
        "eval_label": "fast_zero_shot",
    }
    scored = score_sample(sample)
    assert "reward_confidence" in scored
    assert scored["reward_confidence"]["bg"]["backend"] == "missing"
    assert scored["reward_confidence"]["fg"]["confidence"] <= 0.2
    assert scored["reward_provisional"] is True


def test_not_applicable_reobserve_does_not_create_high_confidence_claim():
    sample = {
        "sample_id": "static",
        "source": "physion_movingcam",
        "template": "unknown",
        "camera_motion": "orbit",
        "video_path": "/tmp/does-not-exist.mp4",
        "candidate_video_path": "/tmp/does-not-exist.mp4",
        "eval_label": "fast_zero_shot",
    }
    scored = score_sample(sample)
    assert scored["components"]["reobs"]["status"] == "not_applicable"
    assert scored["reward_confidence"]["reobs"]["confidence"] <= 0.2


if __name__ == "__main__":
    test_missing_video_reward_is_low_confidence()
    test_not_applicable_reobserve_does_not_create_high_confidence_claim()
