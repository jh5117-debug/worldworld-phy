from __future__ import annotations


def test_prefix5_builder_latent_future_mask_is_strict_future_only():
    from cam_physgeo.dpo.prefix5_pair_builder import latent_future_indices

    idxs = latent_future_indices(total_frames=81, prefix_len=5, temporal_compression=4)
    assert idxs[0] == 2
    assert idxs[-1] == 20
