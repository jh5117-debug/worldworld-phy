from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from cam_physgeo.data.physeditworld_to_lingbot import main
from cam_physgeo.data.lingbot_condition_schema import validate_condition_dir


def test_physeditworld_to_lingbot_smoke(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    for name in ["video.mp4", "action.npy", "poses.npy"]:
        (src / name).write_bytes(b"x")
    np.save(src / "intrinsics.npy", np.array([[100.0, 0.0, 50.0], [0.0, 200.0, 60.0], [0.0, 0.0, 1.0]], dtype=np.float32))
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
        "height": 960,
        "width": 1664,
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
    meta = json.loads((sample_dir / "metadata.json").read_text())
    assert meta["intrinsics_scale"]["status"] == "OK"
    assert meta["intrinsics_scale"]["scale_x"] == 0.5
    assert meta["intrinsics_scale"]["scale_y"] == 0.5
    assert meta["sampling_alignment"]["same_indices_for_action_camera_video"] is True
    scaled = np.load(sample_dir / "intrinsics.npy")
    assert scaled[0, 0] == 50.0
    assert scaled[0, 2] == 25.0
    assert scaled[1, 1] == 100.0
    assert scaled[1, 2] == 30.0


def test_scale_intrinsics_vector(tmp_path: Path):
    from cam_physgeo.data.physeditworld_to_lingbot import scale_intrinsics_array

    scaled = scale_intrinsics_array(np.array([100.0, 200.0, 50.0, 60.0], dtype=np.float32), 0.5, 0.25)
    assert scaled.tolist() == [50.0, 50.0, 25.0, 15.0]
