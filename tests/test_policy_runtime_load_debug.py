
from __future__ import annotations

import json
import time
from pathlib import Path

from cam_physgeo.dpo.policy_runtime_load_debug import StageLogger, run_stage


def test_stage_logger_writes_start_done(tmp_path: Path):
    out = tmp_path / "runtime.jsonl"
    logger = StageLogger(out, heartbeat_seconds=0.01, stage_timeout_seconds=10)
    try:
        run_stage(logger, "unit_stage", lambda: time.sleep(0.02))
    finally:
        logger.close()
    rows = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
    events = [row["event"] for row in rows]
    assert "stage_start" in events
    assert "stage_done" in events
    assert rows[0]["stage"] == "unit_stage"


def test_cuda_stats_without_torch_import():
    import cam_physgeo.dpo.policy_runtime_load_debug as mod

    stats = mod.cuda_stats()
    assert set(stats) == {"allocated_gb", "reserved_gb", "max_allocated_gb", "max_reserved_gb"}
