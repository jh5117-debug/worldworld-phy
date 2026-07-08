from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from cam_physgeo.data.physeditworld_to_lingbot import main
from cam_physgeo.data.lingbot_condition_schema import validate_condition_dir


def _write_tiny_video(path: Path, num_frames: int = 100, width: int = 16, height: int = 12, fps: int = 16) -> None:
    import cv2

    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), float(fps), (width, height))
    assert writer.isOpened()
    for idx in range(num_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[..., 0] = idx % 255
        frame[..., 1] = (idx * 2) % 255
        writer.write(frame)
    writer.release()


def test_physeditworld_to_lingbot_smoke(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    _write_tiny_video(src / "video.mp4")
    np.save(src / "action.npy", np.arange(100 * 2, dtype=np.float32).reshape(100, 2))
    np.save(src / "poses.npy", np.arange(100 * 3, dtype=np.float32).reshape(100, 3))
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
        "num_frames": 100,
        "height": 12,
        "width": 16,
    }
    manifest.write_text(json.dumps(row) + "\n")
    out = tmp_path / "out"
    report = tmp_path / "report.csv"
    summary = tmp_path / "summary.md"
    rc = main(
        [
            "--manifest",
            str(manifest),
            "--output_root",
            str(out),
            "--report",
            str(report),
            "--summary",
            str(summary),
            "--height",
            "6",
            "--width",
            "8",
        ]
    )
    assert rc == 0
    sample_dir = out / "sample0"
    assert validate_condition_dir(sample_dir) == []
    assert "gravity: 4.0g" in (sample_dir / "prompt.txt").read_text()
    meta = json.loads((sample_dir / "metadata.json").read_text())
    assert meta["intrinsics_scale"]["status"] == "OK"
    assert meta["intrinsics_scale"]["scale_x"] == 0.5
    assert meta["intrinsics_scale"]["scale_y"] == 0.5
    assert meta["sampling_alignment"]["same_indices_for_action_camera_video"] is True
    assert meta["action_sampling"]["status"] == "SAMPLED"
    assert meta["camera_sampling"]["status"] == "SAMPLED"
    assert meta["video_sampling"]["status"] == "SAMPLED"
    assert meta["video_sampling"]["output_frame_count"] == 81
    assert meta["video_sampling"]["output_width"] == 8
    assert meta["video_sampling"]["output_height"] == 6
    assert meta["action_sampling"]["output_length"] == 81
    assert meta["camera_sampling"]["output_length"] == 81
    expected_indices = meta["frame_indices"]
    assert np.load(sample_dir / "action.npy").shape == (81, 2)
    assert np.load(sample_dir / "poses.npy").shape == (81, 3)
    assert np.load(sample_dir / "action.npy")[0].tolist() == [0.0, 1.0]
    assert np.load(sample_dir / "action.npy")[-1].tolist() == np.arange(100 * 2, dtype=np.float32).reshape(100, 2)[expected_indices[-1]].tolist()
    scaled = np.load(sample_dir / "intrinsics.npy")
    assert scaled[0, 0] == 50.0
    assert scaled[0, 2] == 25.0
    assert scaled[1, 1] == 100.0
    assert scaled[1, 2] == 30.0

    import cv2

    cap = cv2.VideoCapture(str(sample_dir / "target.mp4"))
    assert cap.isOpened()
    assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == 81
    assert int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) == 8
    assert int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) == 6
    cap.release()


def test_scale_intrinsics_vector(tmp_path: Path):
    from cam_physgeo.data.physeditworld_to_lingbot import scale_intrinsics_array

    scaled = scale_intrinsics_array(np.array([100.0, 200.0, 50.0, 60.0], dtype=np.float32), 0.5, 0.25)
    assert scaled.tolist() == [50.0, 50.0, 25.0, 15.0]


def test_sampled_npy_rejects_too_short_source(tmp_path: Path):
    from cam_physgeo.data.physeditworld_to_lingbot import write_sampled_npy

    src = tmp_path / "short.npy"
    np.save(src, np.zeros((3, 2), dtype=np.float32))
    try:
        write_sampled_npy(src, tmp_path / "out.npy", [0, 4], "action_trace")
    except ValueError as exc:
        assert "cannot cover max frame index" in str(exc)
    else:
        raise AssertionError("expected too-short action trace to be rejected")
