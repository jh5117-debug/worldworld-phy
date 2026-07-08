from pathlib import Path
from cam_physgeo.data.physeditworld_to_lingbot import main as convert_main
from cam_physgeo.eval.physeditworld_baseline_rollout import main


def test_baseline_rollout_blocks_empty_manifest(tmp_path: Path):
    manifest = tmp_path / "empty.jsonl"
    manifest.write_text("")
    report = tmp_path / "report.csv"
    summary = tmp_path / "summary.md"
    rc = main(["--manifest", str(manifest), "--num_conditions", "4", "--output_root", str(tmp_path / "out"), "--report", str(report), "--summary", str(summary)])
    assert rc == 0
    assert "BASELINE_BLOCKED_EMPTY_MANIFEST" in summary.read_text()
