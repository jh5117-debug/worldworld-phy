from __future__ import annotations
from cam_physgeo.utils.geometry import clamp01
from cam_physgeo.utils.video import read_video_frames

def score_reobserve_consistency(sample: dict, landmark_similarity: float|None=None, object_similarity: float|None=None) -> dict:
    motion=str(sample.get('camera_motion') or '')
    applicable=any(k in motion for k in ['reobserve','lookaway','offscreen','yaw'])
    if not applicable: return {'score':1.0,'status':'not_applicable','name':'R_reobs'}
    if landmark_similarity is None and object_similarity is None:
        frames=read_video_frames(sample.get('candidate_video_path') or sample.get('video_path'), max_frames=12, size=(96,64))
        if len(frames)>=4:
            try:
                import numpy as np  # type: ignore
                sim=1.0-float(np.mean(np.abs(frames[0].astype('float32')-frames[-1].astype('float32')))/255.0)
                return {'score':clamp01(sim),'status':'first_last_proxy','name':'R_reobs','landmark_similarity':sim,'todo':'replace with background landmark + object feature matching'}
            except Exception:
                pass
        return {'score':0.0,'status':'missing_video','name':'R_reobs','todo':'compare visible A vs reobserve C with background landmarks and foreground features'}
    vals=[v for v in [landmark_similarity, object_similarity] if v is not None]
    return {'score':clamp01(sum(vals)/len(vals)),'status':'ok','name':'R_reobs','landmark_similarity':landmark_similarity,'object_similarity':object_similarity}
