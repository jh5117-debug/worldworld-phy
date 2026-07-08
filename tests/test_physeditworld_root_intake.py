from argparse import Namespace
from pathlib import Path

from cam_physgeo.orchestration.physeditworld_root_intake import build_statuses, split_roots, write_summary


def args(tmp_path: Path, roots: str = ""):
    return Namespace(
        physeditworld_roots=roots,
        root_candidates_json=str(tmp_path / "root_candidates.json"),
        root_selection_json=str(tmp_path / "root_selection.json"),
        locked_handoff_json=str(tmp_path / "locked_handoff.json"),
        pai_handoff_json=str(tmp_path / "pai_handoff.json"),
        completion_json=str(tmp_path / "completion.json"),
        strict_manifest=str(tmp_path / "all.jsonl"),
        train_manifest=str(tmp_path / "train.jsonl"),
        lingbot_train_manifest=str(tmp_path / "lingbot_train.jsonl"),
    )


def test_split_roots_accepts_colon_and_comma():
    assert split_roots("/a:/b,/c") == ["/a", "/b", "/c"]


def test_intake_waits_for_external_root_without_roots(tmp_path: Path):
    decision, rows = build_statuses(args(tmp_path))
    by_name = {row.name: row for row in rows}
    assert decision == "PHYS_EDITWORLD_ROOT_INTAKE_WAITING_FOR_EXTERNAL_ROOT"
    assert by_name["root_input"].status == "BLOCKED"
    assert by_name["root_selection_lock"].status == "BLOCKED"


def test_intake_needs_lock_when_root_path_is_provided(tmp_path: Path):
    root = tmp_path / "PhysEditWorld_selected_50h"
    root.mkdir()
    decision, rows = build_statuses(args(tmp_path, str(root)))
    by_name = {row.name: row for row in rows}
    assert decision == "PHYS_EDITWORLD_ROOT_INTAKE_ROOTS_PROVIDED_NEED_LOCK"
    assert by_name["root_input"].status == "PASS"
    assert by_name["root_selection_lock"].status == "BLOCKED"


def test_intake_summary_warns_against_false_positive_roots(tmp_path: Path):
    out = tmp_path / "intake.md"
    decision, rows = build_statuses(args(tmp_path))
    write_summary(out, decision, rows)
    text = out.read_text()
    assert "Do not provide VideoPHY/Wan result folders" in text
    assert "run_physeditworld_locked_handoff_sequence.sh" in text
