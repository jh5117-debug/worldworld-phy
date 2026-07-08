from pathlib import Path

from cam_physgeo.dpo.physeditworld_tiny_dpo_probe import count_jsonl, read_decision, visible_gpu_status


def test_tiny_dpo_count_jsonl(tmp_path: Path):
    p = tmp_path / "pairs.jsonl"
    p.write_text("{}\n")
    assert count_jsonl(p) == 1


def test_tiny_dpo_decision_json(tmp_path: Path):
    p = tmp_path / "gate.json"
    p.write_text('{"decision":"READY_FOR_TINY_ANCHORED_DPO"}')
    assert read_decision(p) == "READY_FOR_TINY_ANCHORED_DPO"


def test_tiny_dpo_gpu_policy(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "4,7")
    _, status = visible_gpu_status()
    assert status == "GPU_POLICY_PASS"
