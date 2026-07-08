from pathlib import Path

from cam_physgeo.dpo.physeditworld_tiny_dpo_probe import count_jsonl, main, read_decision, visible_gpu_status


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


def test_tiny_dpo_blocks_without_pair_validation(tmp_path: Path, monkeypatch):
    pair_manifest = tmp_path / "pairs.jsonl"
    pair_manifest.write_text(("{}\n" * 100), encoding="utf-8")
    pair_gate = tmp_path / "gate.md"
    pair_gate.write_text("Decision: `READY_FOR_TINY_ANCHORED_DPO`\n", encoding="utf-8")
    pair_validation = tmp_path / "pair_validation.json"
    pair_validation.write_text('{"decision":"PHYS_EDITWORLD_PAIR_MANIFEST_BLOCKED_EMPTY"}', encoding="utf-8")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "4")
    code = main(
        [
            "--pair_manifest",
            str(pair_manifest),
            "--pair_gate_summary",
            str(pair_gate),
            "--pair_validation",
            str(pair_validation),
            "--output_root",
            str(tmp_path / "out"),
            "--report",
            str(tmp_path / "metrics.csv"),
            "--decision",
            str(tmp_path / "decision.json"),
            "--summary",
            str(tmp_path / "summary.md"),
            "--dry_run",
        ]
    )
    assert code == 0
    assert "TINY_DPO_BLOCKED_PAIR_VALIDATION" in (tmp_path / "summary.md").read_text(encoding="utf-8")
