import numpy as np
from cam_physgeo.dpo.preference_protocol_v1 import quality_floor, reward_from_metrics, local_corrupt_future, FUTURE_FRAME_INDICES

def test_reward_and_quality_floor_medium_values():
    metric = {"ssim": "0.84", "psnr": "16.0", "freeze_rate": "0.0", "blur_laplacian": "60", "flicker_proxy": "0.002"}
    reward = reward_from_metrics(metric, "stageA_final")
    ok, reasons = quality_floor(reward, metric)
    assert ok, reasons
    assert 0.0 <= reward["R_total"] <= 1.0
    assert reward["P_freeze"] == 0.0

def test_future_indices_are_v2v5():
    assert FUTURE_FRAME_INDICES[0] == 5
    assert FUTURE_FRAME_INDICES[-1] == 80
    assert len(FUTURE_FRAME_INDICES) == 76

def test_local_corruption_preserves_length_and_region_metadata():
    frames = [np.full((64, 96, 3), 120, np.uint8) for _ in range(76)]
    out, meta = local_corrupt_future(frames, "object_identity_change_local")
    assert len(out) == 76
    assert "affected_region" in meta
    assert meta["affected_time_span"]["raw_frame_start"] >= 5
