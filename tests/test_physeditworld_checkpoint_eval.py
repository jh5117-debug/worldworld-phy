from pathlib import Path

from cam_physgeo.eval.physeditworld_checkpoint_eval import count_jsonl, parse_steps, visible_gpu_status


def test_parse_steps():
    assert parse_steps("0,500, 1000") == ["0", "500", "1000"]


def test_count_jsonl_missing(tmp_path: Path):
    assert count_jsonl(tmp_path / "missing.jsonl") is None


def test_visible_gpu_blocks_forbidden(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "3")
    _, status = visible_gpu_status()
    assert status.startswith("FORBIDDEN_GPU_VISIBLE")
