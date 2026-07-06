from cam_physgeo.orchestration.gate_checks_v13b import check_only_gpu45

def test_check_only_gpu45():
    assert check_only_gpu45([4])
    assert check_only_gpu45([5])
    assert not check_only_gpu45([6])
    assert not check_only_gpu45([4, 6])
