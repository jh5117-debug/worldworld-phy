import json

from cam_physgeo.orchestration.physeditworld_root_submission_template import (
    FIELDS,
    REQUIRED_EVIDENCE,
    build_summary,
    default_rows,
    write_json,
    write_markdown,
    write_tsv,
)


def test_template_fields_include_action_camera_gravity_replay():
    fields = set(FIELDS)
    assert "action_trace_glob" in fields
    assert "camera_trajectory_or_poses_glob" in fields
    assert "intrinsics_glob" in fields
    assert "gravity_label_or_metadata_glob" in fields
    assert "replay_group_or_matched_replay_glob" in fields
    assert "review_status" in fields


def test_required_evidence_is_not_passive_camera_only():
    evidence = set(REQUIRED_EVIDENCE)
    assert "action_trace_glob" in evidence
    assert "camera_trajectory_or_poses_glob" in evidence
    assert "gravity_label_or_metadata_glob" in evidence
    assert "replay_group_or_matched_replay_glob" in evidence


def test_writes_template_outputs(tmp_path):
    rows = default_rows()
    summary = build_summary(rows)
    tsv = tmp_path / "template.tsv"
    js = tmp_path / "template.json"
    md = tmp_path / "template.md"
    write_tsv(tsv, rows)
    write_json(js, summary, rows)
    write_markdown(md, summary, str(tsv))
    assert "candidate_root" in tsv.read_text()
    payload = json.loads(js.read_text())
    assert payload["decision"] == "PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY"
    assert payload["safety"]["does_not_copy_delete_train_or_use_gpu"] is True
    text = md.read_text()
    assert "PHYS_EDITWORLD_ROOTS" in text
    assert "Do not point" in text
