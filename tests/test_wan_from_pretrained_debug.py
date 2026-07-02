from __future__ import annotations
import json
from pathlib import Path
from cam_physgeo.dpo.wan_from_pretrained_debug import JsonlLogger, run_stage, cpu_rss_gb

def test_jsonl_logger_writes_start_done(tmp_path: Path):
    out = tmp_path / "stage.jsonl"
    logger = JsonlLogger(out, heartbeat_seconds=0.01, stage_timeout_seconds=10)
    try:
        run_stage(logger, "unit", lambda: None)
    finally:
        logger.close()
    rows = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
    assert rows[0]["event"] == "stage_start"
    assert rows[-1]["event"] == "stage_done"

def test_cpu_rss_gb_is_float():
    assert isinstance(cpu_rss_gb(), float)
