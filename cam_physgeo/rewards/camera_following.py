from __future__ import annotations
from cam_physgeo.utils.camera import camera_motion_stats
from cam_physgeo.utils.geometry import clamp01
from cam_physgeo.utils.video import frame_motion_magnitude

def score_camera_following(sample: dict, generated_bg_flow: float|None=None) -> dict:
    stats=camera_motion_stats(sample.get('poses_path'))
    if (not stats.get('available') or float(stats.get('translation_total') or 0.0) <= 1e-8) and sample.get('camera_position_path'):
        pos_stats=camera_motion_stats(sample.get('camera_position_path'))
        if pos_stats.get('available'):
            stats=pos_stats
    expected=stats.get('translation_total')
    if generated_bg_flow is None:
        proxy=frame_motion_magnitude(sample.get('candidate_video_path') or sample.get('video_path'), max_frames=12)
        if proxy.get('available'):
            generated_bg_flow=float(proxy.get('mean_absdiff') or 0.0)
    if expected is None or generated_bg_flow is None:
        return {'score':0.0,'status':'missing_camera_or_video','name':'R_cam','camera_stats':stats,'todo':'compare generated background flow direction/magnitude with pose-induced flow'}
    if expected < 1e-5:
        score=clamp01(1.0-generated_bg_flow/0.08)
    else:
        # Normalize camera translation to a loose frame-diff range; this is a proxy until RAFT/depth residuals are active.
        expected_proxy=clamp01(float(expected)*4.0)
        ratio=generated_bg_flow/(expected_proxy+1e-6)
        score=clamp01(1.0-abs(1.0-ratio))
    return {'score':score,'status':'proxy_frame_diff','name':'R_cam','expected_motion':expected,'generated_bg_flow':generated_bg_flow,'camera_stats':stats}
