from __future__ import annotations
from cam_physgeo.utils.geometry import score_from_error
from cam_physgeo.utils.masks import default_background_mask_note
from cam_physgeo.utils.video import frame_motion_magnitude

def score_background_rigid_consistency(sample: dict, observed_flow_error: float|None=None) -> dict:
    if observed_flow_error is None:
        motion=frame_motion_magnitude(sample.get('candidate_video_path') or sample.get('video_path'), max_frames=12)
        if motion.get('available'):
            # Fallback proxy: real rigid-flow scoring is enabled when flow/depth backends are present.
            # Nonzero, smooth background motion is treated as weak evidence instead of a hard failure.
            score=score_from_error(float(motion.get('max_absdiff') or 0.0)-float(motion.get('mean_absdiff') or 0.0), scale=0.20)
            return {'score':score,'status':'proxy_frame_diff','name':'R_bg','mask_policy':default_background_mask_note(sample),'motion_proxy':motion,'todo':'replace proxy with optical-flow/depth rigid residual when backends are enabled'}
        return {'score':0.0,'status':'missing_video','name':'R_bg','mask_policy':default_background_mask_note(sample),'todo':'estimate optical flow/depth and compare to known-camera rigid flow'}
    return {'score':score_from_error(observed_flow_error, scale=2.0),'status':'ok','name':'R_bg','observed_flow_error':observed_flow_error}
