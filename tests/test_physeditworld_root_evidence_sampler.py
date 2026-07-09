from cam_physgeo.orchestration.physeditworld_root_evidence_sampler import derive_decision, sample_row
from cam_physgeo.orchestration.physeditworld_root_submission_template import FIELDS


def test_waiting_for_unfilled_candidate_root():
    row = {field: "" for field in FIELDS}
    out = sample_row(1, row, 2)
    assert out[0].status == "WAITING_FOR_FILLED_TEMPLATE"
    assert derive_decision(out) == "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE"


def test_sampler_rejects_recursive_globs(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    row = {field: "x" for field in FIELDS}
    row.update({
        "candidate_root": str(root),
        "video_or_frames_glob": "**/*.mp4",
        "action_trace_glob": "actions/*.json",
        "camera_trajectory_or_poses_glob": "poses/*.json",
        "intrinsics_glob": "intrinsics/*.json",
        "gravity_label_or_metadata_glob": "gravity/*.json",
        "replay_group_or_matched_replay_glob": "replay/*.json",
    })
    out = sample_row(1, row, 2)
    assert any(row.status == "RECURSIVE_GLOB_REJECTED" for row in out)


def test_sampler_ready_when_all_required_fields_have_samples(tmp_path):
    root = tmp_path / "root"
    dirs = {
        "video_or_frames_glob": "videos",
        "action_trace_glob": "actions",
        "camera_trajectory_or_poses_glob": "poses",
        "intrinsics_glob": "intrinsics",
        "gravity_label_or_metadata_glob": "gravity",
        "replay_group_or_matched_replay_glob": "replay",
    }
    for dirname in dirs.values():
        d = root / dirname
        d.mkdir(parents=True)
        (d / "one.json").write_text("{}")
    row = {field: "" for field in FIELDS}
    row["candidate_root"] = str(root)
    for field, dirname in dirs.items():
        row[field] = f"{dirname}/*.json"
    out = sample_row(1, row, 1)
    assert derive_decision(out) == "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_READY_FOR_SCHEMA_PROBE"
    assert all(sample.status == "PASS" for sample in out)
