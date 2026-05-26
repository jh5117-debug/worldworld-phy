from __future__ import annotations
from cam_physgeo.utils.camera import camera_motion_stats
from cam_physgeo.utils.geometry import clamp01
from cam_physgeo.utils.video import frame_motion_magnitude

def score_freeze_penalty(sample: dict, generated_bg_flow: float|None=None, generated_fg_flow: float|None=None, expected_fg_motion: float|None=None) -> dict:
    cam=camera_motion_stats(sample.get('poses_path')); expected_cam=cam.get('translation_total') or 0.0; penalty=0.0; reasons=[]
    if generated_bg_flow is None:
        proxy=frame_motion_magnitude(sample.get('candidate_video_path') or sample.get('video_path'), max_frames=12)
        if proxy.get('available'):
            generated_bg_flow=float(proxy.get('mean_absdiff') or 0.0)
    if generated_bg_flow is None: reasons.append('missing_generated_bg_flow')
    elif expected_cam>1e-4 and generated_bg_flow<0.005: penalty+=0.5; reasons.append('camera_expected_but_background_nearly_static')
    elif expected_cam<=1e-4 and generated_bg_flow<0.002 and str(sample.get('template')) in {'drop','collision','roll'}: penalty+=0.25; reasons.append('dynamic_template_but_video_nearly_static')
    if expected_fg_motion is not None and generated_fg_flow is not None and expected_fg_motion>1e-4 and generated_fg_flow<0.05*expected_fg_motion: penalty+=0.5; reasons.append('foreground_expected_but_nearly_static')
    return {'penalty':clamp01(penalty),'status':'ok','name':'P_freeze','reasons':reasons,'camera_stats':cam,'generated_bg_flow':generated_bg_flow}
