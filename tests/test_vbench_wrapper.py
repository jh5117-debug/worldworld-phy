from cam_physgeo.eval.metrics_vbench import compute_vbench_if_available, vbench_backend_status


def test_vbench_wrapper_returns_structured_status() -> None:
    status = vbench_backend_status()
    assert status.status in {"AVAILABLE", "BLOCKED_BY_ENV"}
    result = compute_vbench_if_available("missing_a.mp4", "missing_b.mp4")
    assert result["vbench_status"] in {"AVAILABLE", "BLOCKED_BY_ENV"}
    assert "vbench_reason" in result
