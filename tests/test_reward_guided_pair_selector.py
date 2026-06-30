from cam_physgeo.dpo.reward_guided_pair_selector import (
    alignment_decision,
    compute_total_reward,
    normalized_reward_vector,
    reward_margin,
    subreward_margins,
)


def test_reward_margin_penalizes_blur_and_freeze():
    winner = normalized_reward_vector({"R_bg": 1, "R_cam": 1, "R_fg": 1, "R_phys": 1, "R_reobs": 1, "R_quality": 1})
    loser = normalized_reward_vector({"R_bg": 0.8, "R_cam": 0.8, "R_fg": 0.8, "R_phys": 0.8, "R_reobs": 0.8, "R_quality": 0.9, "P_freeze": 0.1, "P_blur": 0.2})
    assert compute_total_reward(winner) > compute_total_reward(loser)
    assert reward_margin(winner, loser) > 0.1


def test_subreward_alignment_passes_expected_drop():
    winner = {"R_bg": 1.0, "R_cam": 1.0, "R_fg": 1.0, "R_phys": 1.0, "R_reobs": 1.0, "R_quality": 1.0, "P_freeze": 0.0}
    loser = {"R_bg": 0.98, "R_cam": 0.70, "R_fg": 0.95, "R_phys": 0.95, "R_reobs": 0.95, "R_quality": 0.95, "P_freeze": 0.0}
    margins = subreward_margins(winner, loser)
    decision = alignment_decision("wrong_camera_motion_local", margins, min_margin=0.05)
    assert decision["aligned"] is True
    assert decision["status"] == "PASS"


def test_subreward_alignment_rejects_mismatch():
    winner = {"R_bg": 1.0, "R_cam": 1.0, "R_fg": 1.0, "R_phys": 1.0, "R_reobs": 1.0, "R_quality": 1.0}
    loser = {"R_bg": 0.70, "R_cam": 0.95, "R_fg": 0.95, "R_phys": 0.95, "R_reobs": 0.95, "R_quality": 0.95}
    decision = alignment_decision("object_deformation_local", subreward_margins(winner, loser), min_margin=0.05)
    assert decision["aligned"] is False
    assert decision["status"] == "REWARD_FAILURE_MISMATCH"
