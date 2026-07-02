from __future__ import annotations

from pathlib import Path

from cam_physgeo.dpo.backend_runtime_ready_debug import StageLogger, cpu_rss_gb, resolve_repo_path


def test_cpu_rss_nonnegative():
    assert cpu_rss_gb() >= 0.0


def test_resolve_repo_path_relative(tmp_path: Path):
    assert resolve_repo_path("a/b.txt", tmp_path) == tmp_path / "a/b.txt"


def test_stage_logger_writes_jsonl(tmp_path: Path):
    out = tmp_path / "events.jsonl"
    logger = StageLogger(out, heartbeat_seconds=1000.0, stage_timeout_seconds=1000.0)
    with logger.stage("x"):
        pass
    text = out.read_text(encoding="utf-8")
    assert "stage_start" in text
    assert "stage_done" in text
