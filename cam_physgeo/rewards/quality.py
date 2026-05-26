from __future__ import annotations
from cam_physgeo.utils.geometry import clamp01
from cam_physgeo.utils.video import blur_brightness_flicker

def score_quality(sample: dict, blur_score: float|None=None, flicker_score: float|None=None, brightness_ok: float|None=None) -> dict:
    vals=[v for v in [blur_score, flicker_score, brightness_ok] if v is not None]
    if not vals:
        q=blur_brightness_flicker(sample.get('candidate_video_path') or sample.get('video_path'), max_frames=16)
        if not q.get('available'):
            return {'score':0.0,'status':'missing_video','name':'R_quality','todo':'compute blur, brightness, saturation, temporal flicker'}
        blur=clamp01(float(q.get('blur_var_mean') or 0.0)/120.0)
        bright=1.0-abs(float(q.get('brightness_mean') or 0.5)-0.5)*2.0
        sat=clamp01(float(q.get('saturation_mean') or 0.0)/0.12)
        flicker=1.0-clamp01(float(q.get('brightness_flicker') or 0.0)/0.12)
        return {'score':clamp01((blur+bright+sat+flicker)/4.0),'status':'cv2_proxy','name':'R_quality','quality_proxy':q}
    return {'score':clamp01(sum(vals)/len(vals)),'status':'ok','name':'R_quality','blur_score':blur_score,'flicker_score':flicker_score,'brightness_ok':brightness_ok}
