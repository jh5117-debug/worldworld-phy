from pathlib import Path

from cam_physgeo.orchestration.gpu_status import parse_nvidia_smi_csv, parse_pmon, choose_idle_gpu, query_gpu_status
from cam_physgeo.orchestration.job_specs_v12d import default_jobs, build_command
from cam_physgeo.orchestration.gpu_scheduler_v12d import load_simple_yaml


def test_parse_gpu_csv_and_choose_allowed_idle():
    text = "index, memory.used [MiB], memory.total [MiB], utilization.gpu [%]\n4, 1 MiB, 97871 MiB, 0 %\n5, 2000 MiB, 97871 MiB, 0 %\n0, 1 MiB, 97871 MiB, 0 %\n"
    gpus = parse_nvidia_smi_csv(text)
    status = {"gpus": {str(k): v.to_dict() for k, v in gpus.items()}}
    for idx, info in status["gpus"].items():
        i = int(idx)
        info["is_allowed"] = i in {4, 5}
        info["is_forbidden"] = i == 0
        info["is_idle"] = i == 4
    assert choose_idle_gpu(status, [4, 5]) == 4


def test_parse_pmon():
    text = "# gpu pid type sm mem enc dec jpg ofa command\n    4 123 C 99 0 - - - - python3\n    5 - - - - - - - - -\n"
    pmon = parse_pmon(text)
    assert pmon[4][0]["pid"] == 123
    assert 5 not in pmon


def test_job_command_uses_process_local_gpu_zero():
    job = [j for j in default_jobs() if j["job_id"] == "v12c_winner_detached_preference_s_pass4"][0]
    cmd = build_command(job, 7)
    assert "--gpu" in cmd
    assert cmd[cmd.index("--gpu") + 1] == "0"
    assert "winner_detached_preference" in cmd


def test_load_simple_yaml(tmp_path: Path):
    p = tmp_path / "cfg.yaml"
    p.write_text("allowed_physical_gpus: [4,5,6,7]\nheartbeat_seconds: 60\nkill_unknown_process: false\n")
    cfg = load_simple_yaml(p)
    assert cfg["allowed_physical_gpus"] == [4, 5, 6, 7]
    assert cfg["heartbeat_seconds"] == 60
    assert cfg["kill_unknown_process"] is False
