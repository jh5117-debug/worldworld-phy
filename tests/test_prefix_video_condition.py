from __future__ import annotations

import torch

from cam_physgeo.eval.prefix_video_condition import (
    build_condition_video,
    build_wan_prefix_mask,
    latent_visible_indices,
    validate_prefix_plan,
)


def test_prefix_condition_zeros_future_and_keeps_five_frames():
    video = torch.randn(3, 81, 8, 8)
    condition, visible = build_condition_video(video, prefix_len=5, num_frames=81)
    assert condition.shape == video.shape
    assert torch.allclose(condition[:, :5], video[:, :5])
    assert condition[:, 5:].abs().sum().item() == 0
    assert visible[:5].all().item()
    assert not visible[5:].any().item()


def test_wan_prefix_mask_marks_prefix_touched_latents():
    mask, info = build_wan_prefix_mask(
        num_frames=81,
        prefix_len=5,
        latent_frames=21,
        latent_height=2,
        latent_width=3,
        device="cpu",
        dtype=torch.float32,
    )
    assert info.visible_latent_indices == (0, 1)
    assert info.future_frame_indices[0] == 5
    assert info.future_frame_indices[-1] == 80
    assert mask.shape == (4, 21, 2, 3)
    assert mask[:, :2].sum().item() == 4 * 2 * 2 * 3
    assert mask[:, 2:].sum().item() == 0


def test_prefix_len_one_is_old_image_condition_not_v2v5():
    assert latent_visible_indices(num_frames=81, prefix_len=1, latent_frames=21) == (0,)
    try:
        validate_prefix_plan(prefix_len=1, prediction_start_frame=1, num_frames=81)
    except ValueError as exc:
        assert "prefix_len=5" in str(exc)
    else:
        raise AssertionError("prefix_len=1 should be rejected for V2V-5")
