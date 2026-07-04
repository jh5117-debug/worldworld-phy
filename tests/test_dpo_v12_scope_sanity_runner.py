from cam_physgeo.dpo.lora_scope_config_v12 import SCOPE_CANDIDATES


def test_scope_sanity_default_scopes_exist():
    for scope in ["L0_camera_r4", "L1_camera_r8", "L2_camera_temporal_r4", "L3_camera_cross_r4"]:
        assert scope in SCOPE_CANDIDATES
