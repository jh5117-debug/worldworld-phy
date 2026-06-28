from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import yaml

from cam_physgeo.dpo.failure_diagnostics import _config


def test_lora_scope_capacity_config_overrides(tmp_path: Path) -> None:
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump({"student_lora_rank": 4, "student_lora_target_groups": ["camera_conditioning"]}))
    args = Namespace(config=str(cfg_path), num_frames=81, height=480, width=832, runtime_device="cuda", device="cuda")
    cfg = _config(args, rank=8, target_groups=["camera_conditioning", "self_attention"], block_end=4)
    assert cfg["student_lora_rank"] == 8
    assert cfg["student_lora_alpha"] == 8
    assert cfg["student_lora_target_groups"] == ["camera_conditioning", "self_attention"]
    assert cfg["student_lora_block_end"] == 4
