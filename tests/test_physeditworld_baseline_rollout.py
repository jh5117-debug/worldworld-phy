import os
from pathlib import Path

from cam_physgeo.eval.physeditworld_baseline_rollout import main, visible_gpu_status


def test_baseline_rollout_blocks_empty_manifest(tmp_path: Path):
    manifest = tmp_path / "empty.jsonl"
    manifest.write_text("")
    report = tmp_path / "report.csv"
    summary = tmp_path / "summary.md"
    rc = main(["--manifest", str(manifest), "--num_conditions", "4", "--output_root", str(tmp_path / "out"), "--report", str(report), "--summary", str(summary)])
    assert rc == 0
    assert "BASELINE_BLOCKED_EMPTY_MANIFEST" in summary.read_text()


def test_baseline_rollout_requires_validated_manifest(tmp_path: Path):
    manifest = tmp_path / "nonempty.jsonl"
    manifest.write_text('{"sample_id":"s0","gravity_label":"1g"}\n', encoding="utf-8")
    report = tmp_path / "report.csv"
    summary = tmp_path / "summary.md"
    rc = main(
        [
            "--manifest",
            str(manifest),
            "--num_conditions",
            "4",
            "--output_root",
            str(tmp_path / "out"),
            "--report",
            str(report),
            "--summary",
            str(summary),
            "--manifest_validation",
            str(tmp_path / "missing_validation.json"),
        ]
    )
    assert rc == 0
    text = summary.read_text(encoding="utf-8")
    assert "BASELINE_BLOCKED_MANIFEST_VALIDATION" in text
    assert "decision=`MISSING`" in text


def test_baseline_rollout_dry_run_accepts_schema_pass(tmp_path: Path):
    manifest = tmp_path / "nonempty.jsonl"
    manifest.write_text('{"sample_id":"s0","gravity_label":"1g"}\n', encoding="utf-8")
    validation = tmp_path / "validation.json"
    validation.write_text('{"decision":"LINGBOT_MANIFEST_SCHEMA_PASS"}\n', encoding="utf-8")
    report = tmp_path / "report.csv"
    summary = tmp_path / "summary.md"
    rc = main(
        [
            "--manifest",
            str(manifest),
            "--num_conditions",
            "4",
            "--output_root",
            str(tmp_path / "out"),
            "--report",
            str(report),
            "--summary",
            str(summary),
            "--manifest_validation",
            str(validation),
            "--dry_run",
        ]
    )
    assert rc == 0
    assert "BASELINE_READY_DRY_RUN" in summary.read_text(encoding="utf-8")


def test_baseline_rollout_blocks_forbidden_visible_gpu(tmp_path: Path):
    old_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    try:
        manifest = tmp_path / "nonempty.jsonl"
        manifest.write_text('{"sample_id":"s0","gravity_label":"1g"}\n', encoding="utf-8")
        validation = tmp_path / "validation.json"
        validation.write_text('{"decision":"LINGBOT_MANIFEST_SCHEMA_PASS"}\n', encoding="utf-8")
        report = tmp_path / "report.csv"
        summary = tmp_path / "summary.md"
        rc = main(
            [
                "--manifest",
                str(manifest),
                "--num_conditions",
                "4",
                "--output_root",
                str(tmp_path / "out"),
                "--report",
                str(report),
                "--summary",
                str(summary),
                "--manifest_validation",
                str(validation),
                "--dry_run",
            ]
        )
        assert rc == 0
        text = summary.read_text(encoding="utf-8")
        assert "BASELINE_BLOCKED_FORBIDDEN_GPU" in text
        assert "FORBIDDEN_GPU_VISIBLE:0" in text
    finally:
        if old_visible is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = old_visible


def test_visible_gpu_status_allows_only_gpu4_to_7():
    old_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    try:
        os.environ["CUDA_VISIBLE_DEVICES"] = "4,7"
        assert visible_gpu_status()[1] == "GPU_POLICY_PASS"
        os.environ["CUDA_VISIBLE_DEVICES"] = "3,4"
        assert visible_gpu_status()[1] == "FORBIDDEN_GPU_VISIBLE:3"
    finally:
        if old_visible is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = old_visible
