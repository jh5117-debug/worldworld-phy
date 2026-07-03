from cam_physgeo.dpo.pair_factory_v10b_audit import boolish, as_float, infer_source


def test_boolish_and_float():
    assert boolish("yes") is True
    assert boolish("False") is False
    assert as_float("0.5") == 0.5
    assert as_float("BLOCKED", 2.0) == 2.0


def test_infer_source_synthetic():
    pair = {"pair_id": "v10_TypeM_001", "pair_type": "TypeM_v10_synthetic_visible", "loser": {"source": "controlled_visible_synthetic_negative"}}
    src, is_synth, is_rollout, is_controlled = infer_source(pair, {"v10_TypeM_001"}, set())
    assert src == "synthetic_controlled"
    assert is_synth is True
    assert is_rollout is False
    assert is_controlled is True


def test_infer_source_rollout():
    pair = {"pair_id": "v6b_GT_C_001", "pair_type": "GT_C", "loser": {"source": "C_camera_self_temporal_r4"}}
    src, is_synth, is_rollout, is_controlled = infer_source(pair, set(), {"v6b_GT_C_001"})
    assert src == "rollout_derived"
    assert is_rollout is True
