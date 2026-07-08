from __future__ import annotations

from pathlib import Path

from cam_physgeo.data.physeditworld_manifest import discover_samples


def test_discover_sample_with_gravity_action_camera(tmp_path: Path):
    root = tmp_path / "physedit_gravity_0.25"
    root.mkdir()
    video = root / "sample_gravity_0.25.mp4"
    video.write_bytes(b"not a real mp4")
    (root / "action.npy").write_bytes(b"x")
    (root / "camera_trajectory.npy").write_bytes(b"x")
    (root / "intrinsics.npy").write_bytes(b"x")
    rows = discover_samples([tmp_path], target_hours=1, max_depth=3)
    assert len(rows) == 1
    row = rows[0]
    assert row["gravity_label"] == "0.25g"
    assert row["action_trace_path"].endswith("action.npy")
    assert row["camera_trajectory_path"].endswith("camera_trajectory.npy")
    assert row["intrinsics_path"].endswith("intrinsics.npy")
    assert row["status"] in {"VIDEO_DECODE_UNVERIFIED", "SCHEMA_INCOMPLETE"}
