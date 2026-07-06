
from cam_physgeo.dpo.utility_calibration_v14 import compute_metrics

def test_compute_metrics_zero_utility():
    m = compute_metrics(1.0, 1.2, 1.0, 1.2)
    assert abs(m["u_raw"]) < 1e-12
    assert abs(m["win_gap"]) < 1e-12
