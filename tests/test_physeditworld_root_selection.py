from pathlib import Path

from cam_physgeo.data.physeditworld_root_selection import evaluate_roots


def make_strong_root(root: Path):
    root.mkdir(parents=True)
    for name in ["action_trace.json", "camera_trajectory.json", "intrinsics.json", "gravity.json", "replay_group.json", "video.mp4"]:
        (root / name).write_text("x")


def test_no_root_blocks():
    decision, rows, _ = evaluate_roots("", False, 1, 20)
    assert decision == "PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT"
    assert rows[0].status == "BLOCKED"


def test_missing_root_blocks(tmp_path: Path):
    decision, rows, _ = evaluate_roots(str(tmp_path / "missing_physeditworld"), False, 1, 20)
    assert decision == "PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_ROOT_MISSING"
    assert rows[0].status == "BLOCKED"


def test_strong_root_locks(tmp_path: Path):
    root = tmp_path / "PhysEditWorld_selected_50h"
    make_strong_root(root)
    decision, rows, _ = evaluate_roots(str(root), False, 1, 20)
    assert decision == "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED"
    assert rows[0].status == "LOCKED"


def test_weak_root_requires_review(tmp_path: Path):
    root = tmp_path / "maybe_physeditworld"
    root.mkdir()
    (root / "gravity.json").write_text("x")
    (root / "video.mp4").write_text("x")
    decision, rows, _ = evaluate_roots(str(root), False, 1, 20)
    assert decision in {"PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_WEAK_ROOT", "PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_REJECTED_ROOT"}
    assert rows[0].status == "BLOCKED"
