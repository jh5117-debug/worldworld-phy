import numpy as np
from cam_physgeo.dpo.pair_factory_v11_synthetic_generator import corrupt

def test_corrupt_preserves_frame_count():
    frames=[np.zeros((64,64,3), dtype=np.uint8) for _ in range(12)]
    out,bbox,tspan=corrupt(frames,"object_identity_color_shift",0.6,123)
    assert len(out)==len(frames)
    assert len(bbox)==4
    assert tspan[1] > tspan[0]
