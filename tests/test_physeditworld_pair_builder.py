from pathlib import Path

from cam_physgeo.dpo.physeditworld_pair_builder import read_decision, count_jsonl


def test_read_json_decision(tmp_path: Path):
    p = tmp_path / "decision.json"
    p.write_text('{"decision":"WARMUP_GATE_PASS"}')
    assert read_decision(p) == "WARMUP_GATE_PASS"


def test_read_missing_decision(tmp_path: Path):
    assert read_decision(tmp_path / "missing.json") == "MISSING"


def test_count_jsonl(tmp_path: Path):
    p = tmp_path / "rows.jsonl"
    p.write_text("{}\n{}\n")
    assert count_jsonl(p) == 2
