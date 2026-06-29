from cam_physgeo.eval.metrics_fvd import compute_fvd_if_available, fvd_backend_status


def test_fvd_wrapper_never_reports_image_fid_as_fvd() -> None:
    status = fvd_backend_status()
    assert status.status in {"AVAILABLE", "BLOCKED_BY_ENV"}
    result = compute_fvd_if_available("missing_a.mp4", "missing_b.mp4")
    assert result["fvd_status"] in {"AVAILABLE", "BLOCKED_BY_ENV"}
    assert "fvd_reason" in result
    if result["fvd_status"] == "BLOCKED_BY_ENV":
        assert "FID is not reported as video FVD" in result["fvd_reason"] or "No real video FVD backend" in result["fvd_reason"]
