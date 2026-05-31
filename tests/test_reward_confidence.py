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
    assert scored["reward_confidence"]["reobs"]["confidence"] == 0.0


def test_fallback_quality_cannot_dominate_confidence_weighted_total(tmp_path):
    video = tmp_path / "missing.mp4"
    sample = {
        "sample_id": "proxy",
        "source": "physion_movingcam",
        "template": "unknown",
        "camera_motion": "orbit",
        "video_path": str(video),
        "candidate_video_path": str(video),
        "eval_label": "fast_zero_shot",
    }
    scored = score_sample(sample)
    assert scored["reward_confidence"]["quality"]["confidence"] <= 0.25
    assert "R_total_real_backend_only" in scored
    assert "R_total_proxy_only" in scored


def test_clean_gt_metadata_backend_gets_real_confidence(tmp_path):
    video = tmp_path / "clean.mp4"
    video.write_bytes(b"not-a-real-video")
    sample = {
        "sample_id": "clean",
        "source": "physion_movingcam",
        "template": "drop",
        "camera_motion": "orbit",
        "video_path": str(video),
        "candidate_video_path": str(video),
        "poses_path": str(tmp_path / "poses.npy"),
        "intrinsics_path": str(tmp_path / "intrinsics.npy"),
        "eval_label": "clean_gt",
        "clean_gt_backend_coverage": {
            "depth": True,
            "id_mask": True,
            "camera": True,
            "intrinsics": True,
            "object_state": True,
        },
    }
    scored = score_sample(sample)
    assert scored["reward_confidence"]["bg"]["backend"] == "real"
    assert scored["reward_confidence"]["cam"]["backend"] == "real"
    assert scored["reward_confidence"]["fg"]["backend"] == "real"
    assert scored["reward_confidence"]["phys"]["backend"] == "real"
    assert scored["reward_confidence"]["freeze"]["backend"] == "real"
    assert scored["R_total_real_backend_only"] > 0.0


if __name__ == "__main__":
    test_missing_video_reward_is_low_confidence()
    test_not_applicable_reobserve_does_not_create_high_confidence_claim()
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
        test_fallback_quality_cannot_dominate_confidence_weighted_total(Path(d))
    with TemporaryDirectory() as d:
        test_clean_gt_metadata_backend_gets_real_confidence(Path(d))
