from cam_physgeo.dpo.gap_metrics_v13b import compute_gap_metrics, decide_gap_health

def test_gap_metrics_winner_improves():
    m = compute_gap_metrics(0.8, 1.2, 1.0, 1.0)
    assert m["win_gap"] < 0
    assert m["winner_improvement"] > 0

def test_decide_gap_health_pass():
    assert decide_gap_health({"mean_winner_improvement_post": 0.1, "final_winner_improvement_post": 0.1, "mean_winner_contribution_ratio": 0.5, "mean_loser_dominance": 0.5}) == "TRAINING_SIGNAL_PASS"
