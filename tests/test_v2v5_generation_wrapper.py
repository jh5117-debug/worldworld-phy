from __future__ import annotations

import torch

from cam_physgeo.eval.v2v5_generation_wrapper import assert_v2v5_generation_plan, build_prefix_y_for_pipe


class FakeVae:
    def __init__(self):
        self.inputs = []

    def encode(self, videos):
        self.inputs.append(videos[0].detach().clone())
        return [torch.zeros(16, 21, 2, 2)]


class FakePipe:
    def __init__(self):
        self.vae = FakeVae()
        self.device = torch.device("cpu")


def test_build_prefix_y_for_pipe_uses_five_prefix_frames_and_zero_future():
    pipe = FakePipe()
    video = torch.randn(3, 81, 16, 16)
    y, proof = build_prefix_y_for_pipe(
        pipe,
        prefix_video=video,
        prefix_len=5,
        num_frames=81,
        latent_height=2,
        latent_width=2,
        resize_hw=(16, 16),
    )
    encoded = pipe.vae.inputs[0]
    assert torch.allclose(encoded[:, :5], video[:, :5])
    assert encoded[:, 5:].abs().sum().item() == 0
    assert y.shape == (20, 21, 2, 2)
    assert proof.prefix_len == 5
    assert proof.condition_mode == "v2v_prefix_5"
    assert proof.visible_latent_indices == (0, 1)
    assert proof.condition_prefix_nonzero
    assert proof.condition_future_zero


def test_v2v5_generation_plan_rejects_image_only():
    try:
        assert_v2v5_generation_plan(prefix_len=1, prediction_start_frame=1, num_frames=81)
    except ValueError as exc:
        assert "prefix_len=5" in str(exc)
    else:
        raise AssertionError("image-only condition should not pass V2V-5 plan validation")
