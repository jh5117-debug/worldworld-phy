from __future__ import annotations

import json
from pathlib import Path

from cam_physgeo.data.physeditworld_to_lingbot import main
from cam_physgeo.data.lingbot_condition_schema import validate_condition_dir


def test_physeditworld_to_lingbot_smoke(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    for name in ["video.mp4", "action.npy", "poses.npy", "intrinsics.npy"]:
        (src / name).write_bytes(b"x")
    manifest = tmp_path / "manifest.jsonl"
    row = {
        "sample_id": "sample0",
        "replay_group_id": "group0",
        "scene_id": "scene0",
        "action_trace_id": "act0",
        "camera_policy_id": "cam0",
        "gravity_value": 4.0,
        "gravity_label": "4.0g",
        "video_path": str(src / "video.mp4"),
        "action_trace_path": str(src / "action.npy"),
        "camera_trajectory_path": str(src / "poses.npy"),
        "intrinsics_path": str(src / "intrinsics.npy"),
        "num_frames": 81,
    }
    manifest.write_text(json.dumps(row) + "\n")
    out = tmp_path / "out"
    report = tmp_path / "report.csv"
    summary = tmp_path / "summary.md"
    rc = main(["--manifest", str(manifest), "--output_root", str(out), "--report", str(report), "--summary", str(summary)])
    assert rc == 0
    sample_dir = out / "sample0"
    assert validate_condition_dir(sample_dir) == []
    assert "gravity: 4.0g" in (sample_dir / "prompt.txt").read_text()
