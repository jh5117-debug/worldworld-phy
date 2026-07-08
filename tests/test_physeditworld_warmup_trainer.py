from pathlib import Path

from cam_physgeo.training.train_physeditworld_warmup import parse_simple_config, visible_gpu_status


def test_warmup_config_parses_rank32():
    cfg = parse_simple_config("configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml")
    assert cfg["gravity_prompt_only"] is True
    assert cfg["lora_rank"] == 32
    assert cfg["allowed_gpus_declared"] is True


def test_visible_gpu_policy_blocks_forbidden(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    _, status = visible_gpu_status()
    assert status.startswith("FORBIDDEN_GPU_VISIBLE")


def test_visible_gpu_policy_allows_gpu4(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "4")
    _, status = visible_gpu_status()
    assert status == "GPU_POLICY_PASS"
