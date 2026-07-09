import csv
import json
from pathlib import Path

from cam_physgeo.orchestration.physeditworld_root_submission_validate import (
    READY,
    derive_decision,
    read_rows,
    validate_row,
)
from cam_physgeo.orchestration.physeditworld_root_submission_template import FIELDS, default_rows, write_tsv


def test_default_template_waits_for_external_input(tmp_path):
    template = tmp_path / "template.tsv"
    write_tsv(template, default_rows())
    rows = [validate_row(i + 1, row, 5) for i, row in enumerate(read_rows(template))]
    assert rows[0].status == "WAITING_FOR_FILLED_TEMPLATE"
    assert derive_decision(rows, True) == "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE"


def test_rejects_recursive_or_absolute_globs(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    row = {field: "x" for field in FIELDS}
    row.update({
        "candidate_root": str(root),
        "video_or_frames_glob": "**/*.mp4",
        "action_trace_glob": "/abs/actions/*.json",
        "camera_trajectory_or_poses_glob": "poses/*.npy",
        "intrinsics_glob": "intrinsics/*.npy",
        "gravity_label_or_metadata_glob": "gravity/*.json",
        "replay_group_or_matched_replay_glob": "replay/*.json",
        "review_status": "PENDING_EXTERNAL_INPUT",
    })
    out = validate_row(1, row, 5)
    assert out.status == "BLOCKED_EVIDENCE_INCOMPLETE"
    assert "recursive_glob_rejected" in out.skipped_evidence
    assert "absolute_glob_rejected" in out.skipped_evidence


def test_ready_when_required_evidence_matches(tmp_path):
    root = tmp_path / "root"
    for d in ["videos", "actions", "poses", "intrinsics", "gravity", "replay"]:
        (root / d).mkdir(parents=True)
        (root / d / "one.json").write_text("{}")
    row = {field: "" for field in FIELDS}
    row.update({
        "candidate_root": str(root),
        "video_or_frames_glob": "videos/*.json",
        "action_trace_glob": "actions/*.json",
        "camera_trajectory_or_poses_glob": "poses/*.json",
        "intrinsics_glob": "intrinsics/*.json",
        "gravity_label_or_metadata_glob": "gravity/*.json",
        "replay_group_or_matched_replay_glob": "replay/*.json",
        "review_status": "PENDING_EXTERNAL_INPUT",
    })
    out = validate_row(1, row, 5)
    assert out.status == READY
    assert json.loads(out.evidence_counts_json)["video_or_frames_glob"] == 1
