import json

import numpy as np

from cam_physgeo.training.prefix_conditioning import (
    build_prefix_plan,
    enrich_manifest_row,
    zero_future_condition,
)


def test_prefix_len_one_matches_i2v_contract():
    plan = build_prefix_plan(num_frames=9, prefix_len=1, temporal_compression=4)
    assert plan.prediction_start_frame == 1
    assert plan.visible_frame_mask.tolist() == [True, False, False, False, False, False, False, False, False]
    assert plan.loss_frame_mask.tolist() == [False, True, True, True, True, True, True, True, True]
    assert plan.latent_visible_mask.tolist()[0] is True
    assert any(plan.latent_loss_mask.tolist())


def test_prefix_len_five_masks_future_frames():
    frames = np.ones((10, 4, 4, 3), dtype=np.float32)
    conditioned, mask = zero_future_condition(frames, prefix_len=5)
    assert mask.tolist() == [True, True, True, True, True, False, False, False, False, False]
    assert float(conditioned[:5].sum()) == float(frames[:5].sum())
    assert float(conditioned[5:].sum()) == 0.0


def test_manifest_enrichment_future_only_indices():
    row = {"sample_id": "s0", "target_video": "video.mp4", "poses": "poses.npy", "intrinsics": "intrinsics.npy"}
    enriched = enrich_manifest_row(row, prefix_len=5, num_frames=9, temporal_compression=4)
    assert enriched["prefix_len"] == 5
    assert enriched["prediction_start_frame"] == 5
    assert enriched["loss_frame_indices"] == [5, 6, 7, 8]
    assert enriched["reward_frame_indices"] == [5, 6, 7, 8]
    assert enriched["target_frame_indices"] == list(range(9))
    assert enriched["eval_future_only"] is True
    assert enriched["full_target_video_path"] == "video.mp4"

