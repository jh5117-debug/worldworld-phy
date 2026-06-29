from cam_physgeo.dpo.localdpo_mask import build_localdpo_mask, raw_span_to_latent_indices


def test_raw_span_excludes_prefix_slots() -> None:
    assert raw_span_to_latent_indices(5, 80, prediction_start_frame=5) == list(range(2, 21))


def test_region_mask_not_full_or_empty() -> None:
    pair = {
        "pair_id": "p",
        "condition": {"prediction_start_frame": 5},
        "loser": {
            "affected_region": {"x0": 0, "x1": 299, "y0": 0, "y1": 480},
            "affected_time_span": {"raw_frame_start": 5, "raw_frame_end": 80},
        },
    }
    result = build_localdpo_mask(pair)
    assert result.status == "ok"
    assert result.spatial_mask_available
    assert 0.0 < result.spatial_mask_ratio < 0.98
    assert result.latent_temporal_indices[0] >= 2
