from __future__ import annotations

from cam_physgeo.dpo.prefix5_pair_builder import frame_mask, future_indices, latent_future_indices, prefix_indices


def test_prefix5_future_masks_are_zero_indexed():
    masks = frame_mask(total_frames=81, prefix_len=5)
    assert masks["prefix_frame_indices"] == [0, 1, 2, 3, 4]
    assert masks["loss_frame_indices"][0] == 5
    assert masks["loss_frame_indices"][-1] == 80
    assert len(masks["loss_frame_indices"]) == 76
    assert masks["reward_frame_indices"] == masks["loss_frame_indices"]


def test_future_indices_reject_invalid_prefix():
    assert prefix_indices(5) == [0, 1, 2, 3, 4]
    assert future_indices(5, 8) == [5, 6, 7]


def test_latent_future_indices_do_not_overflow():
    idxs = latent_future_indices(total_frames=81, prefix_len=5, temporal_compression=4)
    assert min(idxs) == 1
    assert max(idxs) == 20
