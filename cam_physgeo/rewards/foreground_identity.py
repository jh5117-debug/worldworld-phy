from __future__ import annotations
from cam_physgeo.utils.geometry import clamp01
from cam_physgeo.utils.video import frame_motion_magnitude

def score_foreground_identity(sample: dict, feature_similarity: float|None=None, shape_change: float|None=None) -> dict:
    if feature_similarity is None and shape_change is None:
        motion=frame_motion_magnitude(sample.get('candidate_video_path') or sample.get('video_path'), max_frames=12)
        if sample.get('has_id_mask') or sample.get('id_path'):
            return {'score':0.5,'status':'mask_available_backend_pending','name':'R_fg','motion_proxy':motion,'todo':'use ID mask plus DINO/V-JEPA features for identity/shape stability'}
        if motion.get('available'):
            score=clamp01(1.0-float(motion.get('max_absdiff') or 0.0)*0.5)
            return {'score':score,'status':'global_motion_proxy','name':'R_fg','motion_proxy':motion,'todo':'use DINO/V-JEPA features plus mask area, bbox, contour stability'}
        return {'score':0.0,'status':'missing_video','name':'R_fg','todo':'use DINO/V-JEPA features plus mask area, bbox, contour stability'}
    score=1.0
    if feature_similarity is not None: score*=clamp01(feature_similarity)
    if shape_change is not None: score*=clamp01(1.0-shape_change)
    return {'score':score,'status':'ok','name':'R_fg','feature_similarity':feature_similarity,'shape_change':shape_change}
