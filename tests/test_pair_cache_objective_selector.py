from cam_physgeo.dpo.pair_cache_objective_selector import compute_pair_weight


def test_pair_weight_downweights_nonpositive_delta_ref():
    assert compute_pair_weight(-0.1, 0.2) == 0.1
    assert compute_pair_weight(0.0, 0.2) == 0.1


def test_pair_weight_clips_positive_ratio():
    assert compute_pair_weight(0.01, 0.2) == 0.5
    assert compute_pair_weight(1.0, 0.2) == 2.0
    assert compute_pair_weight(0.2, 0.2) == 1.0

