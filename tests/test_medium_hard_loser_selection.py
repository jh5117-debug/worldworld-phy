from cam_physgeo.dpo.preference_protocol_v1 import codex_rollout_scores, rollout_failure_tags

def test_rollout_failure_tags_are_explicit():
    reward = {"R_cam": 0.6, "R_fg": 0.6, "R_phys": 0.6, "P_freeze": 0.0}
    tags = rollout_failure_tags("dpo_step20", reward)
    assert "object_duplicate" in tags
    assert "wrong_camera_motion" in tags
    scores = codex_rollout_scores({"R_quality": 0.7}, tags)
    assert scores["visual_quality"] == 2
    assert scores["camera_following"] == 1
