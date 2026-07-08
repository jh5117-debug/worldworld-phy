from pathlib import Path

from cam_physgeo.data.physeditworld_root_schema_probe import classify_root, overall_decision


def make_strong_schema(root: Path):
    root.mkdir(parents=True)
    (root / "video.mp4").write_text("x")
    (root / "action_trace.json").write_text("x")
    (root / "camera_trajectory.json").write_text("x")
    (root / "intrinsics.json").write_text("x")
    (root / "gravity.json").write_text("x")
    (root / "replay_group.json").write_text("x")


def test_probe_waits_for_root():
    row = classify_root("", max_depth=1, max_files=20)
    assert row.decision == "PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT"
    assert row.status == "BLOCKED"


def test_probe_strong_schema_ready(tmp_path: Path):
    root = tmp_path / "PhysEditWorld_selected_50h"
    make_strong_schema(root)
    row = classify_root(str(root), max_depth=1, max_files=20)
    assert row.status == "PASS"
    assert row.decision == "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"
    assert "sample_dir" in row.likely_layouts
    assert overall_decision([row]) == "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"


def test_probe_partial_schema_needs_replay(tmp_path: Path):
    root = tmp_path / "PhysEditWorld_selected_50h"
    root.mkdir()
    (root / "video.mp4").write_text("x")
    (root / "action_trace.json").write_text("x")
    (root / "camera_trajectory.json").write_text("x")
    (root / "gravity.json").write_text("x")
    row = classify_root(str(root), max_depth=1, max_files=20)
    assert row.decision == "PHYS_EDITWORLD_SCHEMA_PROBE_PARTIAL_NEEDS_REPLAY_MAPPING"
    assert "missing_replay_group_metadata" in row.blockers


def test_probe_rejects_video_result_false_positive(tmp_path: Path):
    root = tmp_path / "Wan2.2" / "results" / "PHY_GRAVITY_001"
    root.mkdir(parents=True)
    (root / "output_16s_256p.mp4").write_text("x")
    row = classify_root(str(root), max_depth=1, max_files=20)
    assert row.decision == "PHYS_EDITWORLD_SCHEMA_PROBE_REJECT_FALSE_POSITIVE"
