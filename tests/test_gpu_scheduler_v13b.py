from cam_physgeo.orchestration.gpu_scheduler_v13b import ALLOWED, FORBIDDEN, idle_allowed_gpus, build_command

def test_allowed_forbidden_sets():
    assert ALLOWED == [4, 5]
    assert 6 in FORBIDDEN and 0 in FORBIDDEN

def test_idle_allowed_only_45():
    status = {4: {"memory_used_mb": 0, "utilization_percent": 0}, 5: {"memory_used_mb": 2000, "utilization_percent": 0}, 6: {"memory_used_mb": 0, "utilization_percent": 0}}
    assert idle_allowed_gpus(status) == [4]

def test_command_uses_physical_gpu():
    assert "CUDA_VISIBLE_DEVICES=4" in build_command("S01_winner_detached_pref_low", 4, 10)
