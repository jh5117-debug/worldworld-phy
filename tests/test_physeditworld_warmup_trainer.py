from pathlib import Path

from cam_physgeo.training.train_physeditworld_warmup import main, parse_simple_config, visible_gpu_status


def test_warmup_config_parses_rank32():
    cfg = parse_simple_config("configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml")
    assert cfg["gravity_prompt_only"] is True
    assert cfg["lora_rank"] == 32
    assert cfg["allowed_gpus_declared"] is True


def test_visible_gpu_policy_blocks_forbidden(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    _, status = visible_gpu_status()
    assert status.startswith("FORBIDDEN_GPU_VISIBLE")


def test_visible_gpu_policy_allows_gpu4(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "4")
    _, status = visible_gpu_status()
    assert status == "GPU_POLICY_PASS"


def test_warmup_requires_train_manifest_validation(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "4")
    train = tmp_path / "train.jsonl"
    val = tmp_path / "val.jsonl"
    train.write_text("{}\n", encoding="utf-8")
    val.write_text("{}\n", encoding="utf-8")
    val_validation = tmp_path / "val_validation.json"
    val_validation.write_text('{"decision":"LINGBOT_MANIFEST_SCHEMA_PASS"}\n', encoding="utf-8")
    report = tmp_path / "preflight.csv"
    rc = main(
        [
            "--config",
            "configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml",
            "--manifest",
            str(train),
            "--val_manifest",
            str(val),
            "--manifest_validation",
            str(tmp_path / "missing_train_validation.json"),
            "--val_manifest_validation",
            str(val_validation),
            "--max_steps",
            "5",
            "--output_root",
            str(tmp_path / "out"),
            "--report",
            str(report),
            "--dry_run",
        ]
    )
    assert rc == 0
    summary = report.parent / "preflight_summary.md"
    assert "WARMUP_BLOCKED_MANIFEST_VALIDATION" in summary.read_text(encoding="utf-8")


def test_warmup_dry_run_accepts_schema_pass(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "4")
    train = tmp_path / "train.jsonl"
    val = tmp_path / "val.jsonl"
    train.write_text("{}\n", encoding="utf-8")
    val.write_text("{}\n", encoding="utf-8")
    train_validation = tmp_path / "train_validation.json"
    val_validation = tmp_path / "val_validation.json"
    train_validation.write_text('{"decision":"LINGBOT_MANIFEST_SCHEMA_PASS"}\n', encoding="utf-8")
    val_validation.write_text('{"decision":"LINGBOT_MANIFEST_SCHEMA_PASS"}\n', encoding="utf-8")
    report = tmp_path / "preflight.csv"
    rc = main(
        [
            "--config",
            "configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml",
            "--manifest",
            str(train),
            "--val_manifest",
            str(val),
            "--manifest_validation",
            str(train_validation),
            "--val_manifest_validation",
            str(val_validation),
            "--max_steps",
            "5",
            "--output_root",
            str(tmp_path / "out"),
            "--report",
            str(report),
            "--dry_run",
        ]
    )
    assert rc == 0
    summary = report.parent / "preflight_summary.md"
    assert "WARMUP_DRY_RUN_READY" in summary.read_text(encoding="utf-8")
