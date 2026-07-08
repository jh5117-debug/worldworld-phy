from pathlib import Path


def test_warmup_config_rank32_prompt_only():
    path = Path("configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml")
    text = path.read_text()
    assert "lora_rank: 32" in text
    assert "gravity: prompt_only" in text
    assert "allowed_physical_gpus: [4, 5, 6, 7]" in text
    assert "forbidden_physical_gpus: [0, 1, 2, 3]" in text
    assert "max_steps: 2000" in text
