from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from cam_physgeo.data.lingbot_manifest_validate import main as validate_main, validate_manifest_row
from cam_physgeo.data.physeditworld_to_lingbot import main as convert_main


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


def _build_converted_manifest(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    _write_tiny_video(src / "video.mp4")
    np.save(src / "action.npy", np.arange(100 * 2, dtype=np.float32).reshape(100, 2))
    np.save(src / "poses.npy", np.arange(100 * 3, dtype=np.float32).reshape(100, 3))
    np.save(src / "intrinsics.npy", np.eye(3, dtype=np.float32))
    manifest = tmp_path / "raw.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "sample_id": "sample0",
                "replay_group_id": "group0",
                "scene_id": "scene0",
                "action_trace_id": "act0",
                "camera_policy_id": "cam0",
                "gravity_value": 1.0,
                "gravity_label": "1.0g",
                "video_path": str(src / "video.mp4"),
                "action_trace_path": str(src / "action.npy"),
                "camera_trajectory_path": str(src / "poses.npy"),
                "intrinsics_path": str(src / "intrinsics.npy"),
                "num_frames": 100,
                "height": 12,
                "width": 16,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_out = tmp_path / "lingbot.jsonl"
    rc = convert_main(
        [
            "--manifest",
            str(manifest),
            "--output_root",
            str(tmp_path / "out"),
            "--report",
            str(tmp_path / "report.csv"),
            "--summary",
            str(tmp_path / "summary.md"),
            "--manifest_out",
            str(manifest_out),
            "--height",
            "6",
            "--width",
            "8",
        ]
    )
    assert rc == 0
    return manifest_out


def test_lingbot_manifest_validate_pass(tmp_path: Path):
    manifest = _build_converted_manifest(tmp_path)
    row = json.loads(manifest.read_text(encoding="utf-8").splitlines()[0])
    result = validate_manifest_row(row)
    assert result["status"] == "PASS", result


def test_lingbot_manifest_validate_missing_path_fails(tmp_path: Path):
    manifest = _build_converted_manifest(tmp_path)
    row = json.loads(manifest.read_text(encoding="utf-8").splitlines()[0])
    row["target_video_path"] = str(tmp_path / "missing.mp4")
    result = validate_manifest_row(row)
    assert result["status"] == "FAIL"
    assert "missing_path:target_video_path" in result["error_reason"]


def test_lingbot_manifest_validate_missing_manifest_is_structured(tmp_path: Path):
    rc = validate_main(
        [
            "--manifest",
            str(tmp_path / "missing.jsonl"),
            "--output_csv",
            str(tmp_path / "out.csv"),
            "--output_json",
            str(tmp_path / "out.json"),
            "--summary",
            str(tmp_path / "summary.md"),
        ]
    )
    assert rc == 0
    payload = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert payload["decision"] == "LINGBOT_MANIFEST_BLOCKED_MISSING"
    assert payload["missing_manifest"] is True
