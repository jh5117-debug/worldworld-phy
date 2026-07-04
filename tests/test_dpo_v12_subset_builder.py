from pathlib import Path
from cam_physgeo.dpo.dpo_v12_subset_builder import diverse_select, failure_bucket, reviewed_ready, write_jsonl, read_jsonl


def row(i, failure, source="synthetic_controlled", condition=None):
    return {
        "pair_id": f"p{i}",
        "pair_type": "GT_C" if source == "rollout_derived" else "TypeM_v11_synthetic_visible",
        "pair_source": source,
        "is_rollout_derived": source == "rollout_derived",
        "is_synthetic": source != "rollout_derived",
        "failure_tag": failure,
        "condition": {"condition_id": condition or f"c{i}", "template": "drop", "camera_motion": "orbit"},
        "codex_visual_audit": {"reviewed": True, "is_dpo_ready": True},
        "medium_hard": True,
    }


def test_failure_bucket_mapping():
    assert failure_bucket(row(1, "wrong_camera_motion_visible")) == "wrong_camera"
    assert failure_bucket(row(2, "object_identity_color_shift")) == "identity_change"
    assert failure_bucket(row(3, "collision_response_failure_synthetic")) == "physical_event_failure"


def test_diverse_select_prefers_rollout_and_unique_conditions():
    rows = [row(i, "background_drift_visible") for i in range(10)]
    rows += [row(100 + i, "wrong_camera_motion_visible", "rollout_derived") for i in range(3)]
    selected = diverse_select(rows, 5, rollout_limit=2, max_per_condition=1)
    assert len(selected) == 5
    assert sum(1 for r in selected if r["is_rollout_derived"]) == 2
    assert len({r["condition"]["condition_id"] for r in selected}) == 5


def test_jsonl_roundtrip(tmp_path: Path):
    p = tmp_path / "x.jsonl"
    rows = [row(1, "partial_freeze_foreground")]
    write_jsonl(p, rows)
    loaded = read_jsonl(p)
    assert loaded[0]["pair_id"] == "p1"
    assert reviewed_ready(loaded[0]) is True
