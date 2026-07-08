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


def test_prompt_named_videos_do_not_create_schema_signals(tmp_path: Path):
    root = tmp_path / "VIDEOPHY2" / "physical_ti2v_5b" / "checkpoint-400"
    root.mkdir(parents=True)
    (root / "0001_the_camera_captures_action_replay_under_gravity.mp4").write_text("x")

    rows = rank_candidates([], [str(root)], max_depth=1, max_files=20)

    assert rows[0].status == "REJECT_LIKELY_FALSE_POSITIVE"
    assert rows[0].signals == "video"


def test_results_gravity_videos_without_schema_are_rejected(tmp_path: Path):
    root = tmp_path / "Wan2.2" / "results" / "PHY_GRAVITY_001_Seed42"
    root.mkdir(parents=True)
    (root / "latent_variance.npy").write_text("x")
    (root / "output_16s_256p.mp4").write_text("x")

    rows = rank_candidates([], [str(root)], max_depth=1, max_files=20)

    assert rows[0].status == "REJECT_LIKELY_FALSE_POSITIVE"
    assert "gravity" not in rows[0].signals.split(",")
