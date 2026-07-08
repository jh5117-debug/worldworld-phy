from argparse import Namespace
from pathlib import Path

from cam_physgeo.orchestration.physeditworld_backend_readiness import (
    SCAFFOLD_DECISION,
    check_scaffold_backend,
    check_warmup_config,
    overall_decision,
    parse_warmup_config,
)


def test_warmup_config_requires_prompt_only_rank32(tmp_path: Path):
    cfg = tmp_path / "warmup.yaml"
    cfg.write_text(
        """
condition:
  gravity: prompt_only
trainable:
  lora_rank: 32
gpu_policy:
  allowed_physical_gpus: [4, 5, 6, 7]
  forbidden_physical_gpus: [0, 1, 2, 3]
""",
        encoding="utf-8",
    )
    parsed = parse_warmup_config(cfg)
    assert parsed["gravity_prompt_only"] is True
    assert parsed["lora_rank"] == 32
    statuses = {row.name: row.status for row in check_warmup_config(str(cfg))}
    assert statuses["warmup_config_prompt_only_gravity"] == "PASS"
    assert statuses["warmup_config_lora_rank32"] == "PASS"
    assert statuses["warmup_config_gpu_policy"] == "PASS"


def test_scaffold_marker_blocks_backend(tmp_path: Path):
    source = tmp_path / "baseline.py"
    source.write_text('decision = "BASELINE_BACKEND_NOT_CONNECTED"\n', encoding="utf-8")
    row = check_scaffold_backend("baseline", str(source), "BASELINE_BACKEND_NOT_CONNECTED", "wire backend")
    assert row.status == "BLOCKED"
    assert "BASELINE_BACKEND_NOT_CONNECTED" in row.detail
    assert overall_decision([row]) == SCAFFOLD_DECISION


def test_dependency_block_precedes_scaffold_block(tmp_path: Path):
    source = tmp_path / "baseline.py"
    source.write_text('decision = "BASELINE_BACKEND_NOT_CONNECTED"\n', encoding="utf-8")
    scaffold = check_scaffold_backend("baseline", str(source), "BASELINE_BACKEND_NOT_CONNECTED", "wire backend")
    missing = check_scaffold_backend("missing", str(tmp_path / "missing.py"), "X", "restore file")
    assert overall_decision([scaffold, missing]) == "PHYS_EDITWORLD_BACKEND_BLOCKED_DEPENDENCY"
