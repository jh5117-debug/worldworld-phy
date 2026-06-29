from cam_physgeo.dpo.localdpo_mask import raw_span_to_latent_indices


def test_partial_time_span_maps_inside_future() -> None:
    out = raw_span_to_latent_indices(20, 40, prediction_start_frame=5)
    assert out[0] >= 5
    assert out[-1] <= 10
