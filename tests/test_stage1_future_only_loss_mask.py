from __future__ import annotations

from physical_consistency.stages.stage1_physinone_cam.trainer import _future_latent_start


def test_future_latent_start_for_prefix5_excludes_prefix_touched_slots():
    assert _future_latent_start(prefix_len=5, latent_frames=21, frame_total=81) == 2


def test_future_latent_start_for_image_only_matches_legacy_slice():
    assert _future_latent_start(prefix_len=1, latent_frames=21, frame_total=81) == 1
