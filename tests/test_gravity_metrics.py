from cam_physgeo.eval.gravity_metrics import pairwise_ordering_accuracy, summarize_scalar_error


def test_gravity_ordering_airtime_lower_at_high_g():
    rows = [
        {"replay_group_id": "g", "gravity_value": 0.25, "airtime_sec": 3.0},
        {"replay_group_id": "g", "gravity_value": 4.0, "airtime_sec": 1.0},
    ]
    out = pairwise_ordering_accuracy(rows, "airtime_sec", higher_gravity_lower_value=True)
    assert out["accuracy"] == 1.0


def test_scalar_error():
    out = summarize_scalar_error([{"pred": 1.5, "target": 1.0}], "pred", "target")
    assert out["mean_abs_error"] == 0.5
