from cam_physgeo.dpo.lora_scope_config_v12 import SCOPE_CANDIDATES, apply_scope_to_cfg


def test_scope_candidates_exclude_ffn():
    for spec in SCOPE_CANDIDATES.values():
        assert "ffn" not in spec["target_groups"]


def test_apply_scope_to_cfg_sets_lora_fields():
    cfg = apply_scope_to_cfg({"x": 1}, "L1_camera_r8")
    assert cfg["student_tuning_mode"] == "lora"
    assert cfg["student_lora_rank"] == 8
    assert cfg["student_lora_target_groups"] == ["camera_conditioning"]
