import numpy as np
from cam_physgeo.dpo.preference_protocol_v1 import local_corrupt_future

def test_local_corruption_does_not_require_prefix_frames():
    frames = [np.full((32, 48, 3), i, np.uint8) for i in range(76)]
    out, meta = local_corrupt_future(frames, "background_drift_local")
    assert len(out) == len(frames)
    assert meta["affected_time_span"]["raw_frame_start"] == 5
