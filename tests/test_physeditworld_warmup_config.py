from pathlib import Path

from cam_physgeo.training.train_physeditworld_warmup import main, visible_gpu_status


def test_warmup_config_rank32_prompt_only():
    path = Path("configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml")
    text = path.read_text()
    assert "lora_rank: 32" in text
    assert "gravity: prompt_only" in text
    assert "allowed_physical_gpus: [4, 5, 6, 7]" in text
    assert "forbidden_physical_gpus: [0, 1, 2, 3]" in text
    assert "max_steps: 2000" in text


def test_visible_gpu_status_reports_no_visible_gpu(monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    _, status = visible_gpu_status()
    assert status == "NO_VISIBLE_GPU_SET"


def test_warmup_blocks_no_visible_gpu_for_real_run(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    config = tmp_path / "warmup.yaml"
    config.write_text(
        "gravity: prompt_only\nlora_rank: 32\nmax_steps: 2000\nallowed_physical_gpus: [4, 5, 6, 7]\nforbidden_physical_gpus: [0, 1, 2, 3]\n",
        encoding="utf-8",
    )
    train = tmp_path / "train.jsonl"
    val = tmp_path / "val.jsonl"
    train.write_text("{}\n", encoding="utf-8")
    val.write_text("{}\n", encoding="utf-8")
    train_validation = tmp_path / "train_validation.json"
    val_validation = tmp_path / "val_validation.json"
    train_validation.write_text('{"decision":"LINGBOT_MANIFEST_SCHEMA_PASS"}\n', encoding="utf-8")
    val_validation.write_text('{"decision":"LINGBOT_MANIFEST_SCHEMA_PASS"}\n', encoding="utf-8")
    rc = main(
        [
            "--config",
            str(config),
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
            str(tmp_path / "preflight.csv"),
        ]
    )
    assert rc == 0
    assert "WARMUP_BLOCKED_NO_VISIBLE_GPU" in (tmp_path / "preflight_summary.md").read_text(encoding="utf-8")


def test_warmup_dry_run_allows_no_visible_gpu(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    config = tmp_path / "warmup.yaml"
    config.write_text(
        "gravity: prompt_only\nlora_rank: 32\nmax_steps: 2000\nallowed_physical_gpus: [4, 5, 6, 7]\nforbidden_physical_gpus: [0, 1, 2, 3]\n",
        encoding="utf-8",
    )
    train = tmp_path / "train.jsonl"
    val = tmp_path / "val.jsonl"
    train.write_text("{}\n", encoding="utf-8")
    val.write_text("{}\n", encoding="utf-8")
    validation = tmp_path / "validation.json"
    validation.write_text('{"decision":"LINGBOT_MANIFEST_SCHEMA_PASS"}\n', encoding="utf-8")
    rc = main(
        [
            "--config",
            str(config),
            "--manifest",
            str(train),
            "--val_manifest",
            str(val),
            "--manifest_validation",
            str(validation),
            "--val_manifest_validation",
            str(validation),
            "--max_steps",
            "5",
            "--output_root",
            str(tmp_path / "out"),
            "--report",
            str(tmp_path / "preflight.csv"),
            "--dry_run",
        ]
    )
    assert rc == 0
    assert "WARMUP_DRY_RUN_READY" in (tmp_path / "preflight_summary.md").read_text(encoding="utf-8")

