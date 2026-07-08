from pathlib import Path

from cam_physgeo.dpo.physeditworld_pair_manifest_validate import (
    PASS_DECISION,
    decision_for,
    validate_row,
)


def _touch(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    return str(path)


def test_pair_manifest_validator_accepts_strict_row(tmp_path: Path):
    row = {
        "pair_id": "p0",
        "pair_type": "TypeA",
        "condition_id": "c0",
        "prefix_video_path": _touch(tmp_path / "prefix.mp4"),
        "winner_video_path": _touch(tmp_path / "winner.mp4"),
        "loser_video_path": _touch(tmp_path / "loser.mp4"),
        "contact_sheet_path": _touch(tmp_path / "sheet.jpg"),
        "same_condition": True,
        "same_action": True,
        "same_camera": True,
        "same_intrinsics": True,
        "same_gravity": True,
        "reward_winner": 0.8,
        "reward_loser": 0.2,
        "gravity_metric_winner": 0.7,
        "gravity_metric_loser": 0.1,
        "codex_visual_audit": {"reviewed": True, "written_reason": "visible gravity timing mismatch", "medium_hard": True},
        "winner_bad": False,
        "too_blurry": False,
        "too_collapsed": False,
        "too_subtle": False,
    }
    result = validate_row(row, Path("."), check_paths=True)
    assert result.status == "ready_strict"
    assert result.error_reason == ""
    assert decision_for([result], None, min_pairs=1) == PASS_DECISION


def test_pair_manifest_validator_rejects_unreviewed_loser(tmp_path: Path):
    row = {
        "pair_id": "p0",
        "pair_type": "TypeB",
        "condition_id": "c0",
        "prefix_video_path": _touch(tmp_path / "prefix.mp4"),
        "winner_video_path": _touch(tmp_path / "winner.mp4"),
        "loser_video_path": _touch(tmp_path / "loser.mp4"),
        "contact_sheet_path": _touch(tmp_path / "sheet.jpg"),
        "same_condition": True,
        "same_action": True,
        "same_camera": True,
        "same_intrinsics": True,
        "same_gravity": True,
        "reward_margin": 0.3,
        "gravity_metric_margin": 0.2,
        "reviewed": False,
        "written_reason": "",
        "medium_hard": True,
    }
    result = validate_row(row, Path("."), check_paths=True)
    assert result.status == "rejected"
    assert "reviewed" in result.error_reason
    assert "written_reason" in result.error_reason
    assert decision_for([result], None, min_pairs=1) == "PHYS_EDITWORLD_PAIR_MANIFEST_BLOCKED_INSUFFICIENT_READY"


def test_pair_manifest_validator_blocks_empty_manifest():
    assert decision_for([], None, min_pairs=100) == "PHYS_EDITWORLD_PAIR_MANIFEST_BLOCKED_EMPTY"
