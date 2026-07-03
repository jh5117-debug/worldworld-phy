from cam_physgeo.dpo.pair_cache_objective_runner import decide_status, winner_contribution_ratio


def test_winner_contribution_ratio_bounds():
    assert winner_contribution_ratio(1.0, 0.0) == 1.0
    assert winner_contribution_ratio(0.0, 1.0) == 0.0
    assert 0.49 < winner_contribution_ratio(1.0, 1.0) < 0.51


def test_winner_anchor_status_requires_positive_mean_and_final():
    rows = [
        {"status": "PASS", "winner_improvement_post": 0.1, "winner_contribution_ratio_post": 1.0},
        {"status": "PASS", "winner_improvement_post": 0.2, "winner_contribution_ratio_post": 1.0},
    ]
    assert decide_status("winner_anchor_repeat", rows, 2) == "WINNER_ANCHOR_REPEAT_PASS"
    rows[-1]["winner_improvement_post"] = -0.2
    assert decide_status("winner_anchor_repeat", rows, 2) == "WINNER_ANCHOR_REPEAT_FAIL"

