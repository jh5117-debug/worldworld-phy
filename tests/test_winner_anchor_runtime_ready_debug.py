from __future__ import annotations

import json
import time
from pathlib import Path

from cam_physgeo.dpo.winner_anchor_runtime_ready_debug import StageLogger


def test_stage_logger_writes_start_done(tmp_path: Path):
    out = tmp_path / "runtime.jsonl"
    logger = StageLogger(out, heartbeat_seconds=0.01, stage_timeout_seconds=10)
    try:
        with logger.stage("unit_stage", pair_id="pair0"):
            time.sleep(0.02)
    finally:
        logger.close()
    rows = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
    events = [row["event"] for row in rows]
    assert "stage_start" in events
    assert "stage_done" in events
    assert rows[0]["stage"] == "unit_stage"
