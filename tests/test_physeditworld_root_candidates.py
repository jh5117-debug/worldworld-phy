from pathlib import Path

from cam_physgeo.data.physeditworld_root_candidates import candidate_root, overall_decision, rank_candidates


def test_candidate_root_uses_sample_parent_for_action_file():
    assert candidate_root("/data/sample/action.npy") == "/data/sample"


def test_false_positive_physion_is_rejected(tmp_path: Path):
    sample = tmp_path / "physion_lingbot_inputs" / "case0"
    sample.mkdir(parents=True)
    (sample / "action.npy").write_text("x")
    rows = rank_candidates([str(sample / "action.npy")], [], max_depth=1, max_files=20)
    assert rows[0].status == "REJECT_LIKELY_FALSE_POSITIVE"


def test_explicit_physedit_root_can_be_strong(tmp_path: Path):
    root = tmp_path / "PhysEditWorld_selected_50h"
    root.mkdir()
    for name in ["action_trace.json", "camera_trajectory.json", "intrinsics.json", "gravity.json", "replay_group.json", "video.mp4"]:
        (root / name).write_text("x")
    rows = rank_candidates([], [str(root)], max_depth=1, max_files=20)
    assert rows[0].status == "STRONG_CANDIDATE"
    assert overall_decision(rows) == "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG"
