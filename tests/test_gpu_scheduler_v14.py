from cam_physgeo.orchestration import gpu_scheduler_v14 as sched


def test_gpu_constants_are_v14_only():
    assert sched.ALLOWED_PHYSICAL_GPUS == [4, 5]
    assert set(sched.FORBIDDEN_PHYSICAL_GPUS) == {0, 1, 2, 3, 6, 7}


def test_idle_allowed_gpus_filters_forbidden():
    status = {
        "gpus": {
            "4": {"memory_used_mb": 1, "utilization_percent": 0},
            "5": {"memory_used_mb": 2000, "utilization_percent": 0},
            "6": {"memory_used_mb": 1, "utilization_percent": 0},
        }
    }
    assert sched.idle_allowed_gpus(status, [4, 5], 1000, 10) == [4]


def test_build_state_never_launches_training(tmp_path, monkeypatch):
    monkeypatch.setattr(sched, "query_gpu_status", lambda: {"gpus": {"4": {"memory_used_mb": 1, "utilization_percent": 0}, "5": {"memory_used_mb": 1, "utilization_percent": 0}}})
    decision = tmp_path / "best.json"
    decision.write_text('{"decision":"DPO_RECIPE_NOT_FOUND_V14"}\n')
    state = sched.build_state({"allowed_physical_gpus": [4, 5], "forbidden_physical_gpus": [0, 1, 2, 3, 6, 7]}, tmp_path / "state.json", tmp_path / "heartbeat.jsonl", decision)
    assert state["scheduler_decision"] == "NO_TRAINING_NO_SCALE"
    assert all(job["command"] == "none" for job in state["jobs"])
    assert state["idle_allowed_gpus"] == [4, 5]
