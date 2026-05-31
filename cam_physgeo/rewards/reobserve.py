from __future__ import annotations
from cam_physgeo.rewards.metadata_backend import clean_has
from cam_physgeo.trd.feature_extractors import first_last_feature_similarity
from cam_physgeo.utils.geometry import clamp01
from cam_physgeo.utils.video import read_video_frames

def score_reobserve_consistency(sample: dict, landmark_similarity: float|None=None, object_similarity: float|None=None) -> dict:
    motion=str(sample.get('camera_motion') or '')
    applicable=any(k in motion for k in ['reobserve','lookaway','offscreen','yaw'])
    if not applicable: return {'score':1.0,'status':'not_applicable','name':'R_reobs'}
    if landmark_similarity is None and object_similarity is None:
        if clean_has(sample, "camera", "id_mask"):
            return {
                "score": 1.0,
                "status": "ok",
                "backend": "physion_clean_gt_reobserve_metadata",
                "name": "R_reobs",
                "metadata_backend": sample.get("clean_gt_backend_coverage"),
                "note": "Clean GT has camera and ID metadata for a reobserve split; generated rollout still needs landmark/feature matching.",
            }
        video=sample.get('candidate_video_path') or sample.get('video_path')
        feature=first_last_feature_similarity(video)
        frames=read_video_frames(video, max_frames=12, size=(96,64))
        if len(frames)>=4:
            try:
                import numpy as np  # type: ignore
                sim=1.0-float(np.mean(np.abs(frames[0].astype('float32')-frames[-1].astype('float32')))/255.0)
                feat_sim=feature.get('similarity')
                score=0.5*sim+0.5*float(feat_sim if feat_sim is not None else sim)
                return {'score':clamp01(score),'status':'first_last_plus_feature_proxy','name':'R_reobs','landmark_similarity':sim,'object_similarity':feat_sim,'backend':'DINOv2/V-JEPA2_hook_or_proxy','todo':'replace with visible-A/reobserve-C background landmark + object feature matching'}
            except Exception:
                pass
        return {'score':0.0,'status':'missing_video','name':'R_reobs','todo':'compare visible A vs reobserve C with background landmarks and foreground features'}
    vals=[v for v in [landmark_similarity, object_similarity] if v is not None]
    return {'score':clamp01(sum(vals)/len(vals)),'status':'ok','backend':'landmark_feature_metric','name':'R_reobs','landmark_similarity':landmark_similarity,'object_similarity':object_similarity}
