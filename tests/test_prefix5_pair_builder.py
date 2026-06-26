from __future__ import annotations

from cam_physgeo.dpo.prefix5_pair_builder import CORRUPTION_TYPES, corrupt_future, frame_mask


def test_corruption_types_are_defined():
    assert "background_drift" in CORRUPTION_TYPES
    assert "global_freeze" not in CORRUPTION_TYPES


def test_frame_mask_future_only_contract():
    masks = frame_mask(total_frames=81, prefix_len=5)
    assert set(masks["prefix_frame_indices"]).isdisjoint(masks["loss_frame_indices"])
    assert set(masks["prefix_frame_indices"]).isdisjoint(masks["reward_frame_indices"])
