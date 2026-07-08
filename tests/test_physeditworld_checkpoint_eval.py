from pathlib import Path

from cam_physgeo.eval.physeditworld_checkpoint_eval import main, count_jsonl, parse_steps, visible_gpu_status


def test_parse_steps():
    assert parse_steps("0,500, 1000") == ["0", "500", "1000"]


def test_count_jsonl_missing(tmp_path: Path):
    assert count_jsonl(tmp_path / "missing.jsonl") is None


def test_visible_gpu_blocks_forbidden(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "3")
    _, status = visible_gpu_status()
    assert status.startswith("FORBIDDEN_GPU_VISIBLE")


def test_checkpoint_eval_requires_validated_manifest(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "4")
    manifest = tmp_path / "eval.jsonl"
    manifest.write_text("{}\n", encoding="utf-8")
    checkpoint_root = tmp_path / "ckpt"
    checkpoint_root.mkdir()
    rc = main(
        [
            "--eval_manifest",
            str(manifest),
            "--eval_manifest_validation",
            str(tmp_path / "missing_validation.json"),
            "--checkpoint_root",
            str(checkpoint_root),
            "--output_root",
            str(tmp_path / "out"),
            "--report",
            str(tmp_path / "report.csv"),
            "--gravity_metrics",
            str(tmp_path / "gravity.csv"),
            "--video_audit",
            str(tmp_path / "audit.csv"),
            "--decision",
            str(tmp_path / "decision.json"),
            "--summary",
            str(tmp_path / "summary.md"),
            "--dry_run",
        ]
    )
    assert rc == 0
    assert "CHECKPOINT_EVAL_BLOCKED_MANIFEST_VALIDATION" in (tmp_path / "summary.md").read_text(encoding="utf-8")


def test_checkpoint_eval_dry_run_accepts_schema_pass(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "4")
    manifest = tmp_path / "eval.jsonl"
    manifest.write_text("{}\n", encoding="utf-8")
    validation = tmp_path / "validation.json"
    validation.write_text('{"decision":"LINGBOT_MANIFEST_SCHEMA_PASS"}\n', encoding="utf-8")
    checkpoint_root = tmp_path / "ckpt"
    checkpoint_root.mkdir()
    rc = main(
        [
            "--eval_manifest",
            str(manifest),
            "--eval_manifest_validation",
            str(validation),
            "--checkpoint_root",
            str(checkpoint_root),
            "--output_root",
            str(tmp_path / "out"),
            "--report",
            str(tmp_path / "report.csv"),
            "--gravity_metrics",
            str(tmp_path / "gravity.csv"),
            "--video_audit",
            str(tmp_path / "audit.csv"),
            "--decision",
            str(tmp_path / "decision.json"),
            "--summary",
            str(tmp_path / "summary.md"),
            "--dry_run",
        ]
    )
    assert rc == 0
    assert "CHECKPOINT_EVAL_READY_DRY_RUN" in (tmp_path / "summary.md").read_text(encoding="utf-8")
