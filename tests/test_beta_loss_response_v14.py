
from cam_physgeo.dpo.beta_loss_response_v14 import sigmoid, softplus_neg

def test_beta_math():
    assert abs(sigmoid(0.0) - 0.5) < 1e-12
    assert softplus_neg(0.0) > 0.69 and softplus_neg(0.0) < 0.70

def test_zero_utility_recommendation_is_none(tmp_path):
    import csv
    from cam_physgeo.dpo.beta_loss_response_v14 import sweep
    import argparse

    inp = tmp_path / "zero.csv"
    with inp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["status", "u_raw"])
        w.writeheader()
        w.writerow({"status": "PASS", "u_raw": "0"})
        w.writerow({"status": "PASS", "u_raw": "0"})
    rec = tmp_path / "rec.json"
    result = sweep(argparse.Namespace(input_csv=[str(inp)], output=str(tmp_path / "out.csv"), summary=str(tmp_path / "summary.md"), recommendation=str(rec)))
    assert result["recommendation"]["recommended_utility_type"] == "NONE_ZERO_UTILITY"
    assert result["recommendation"]["recommended_beta"] is None

