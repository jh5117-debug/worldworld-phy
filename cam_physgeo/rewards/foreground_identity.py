from __future__ import annotations
from cam_physgeo.rewards.metadata_backend import clean_has
from cam_physgeo.trd.feature_extractors import first_last_feature_similarity, video_feature_signature
from cam_physgeo.utils.geometry import clamp01
from cam_physgeo.utils.video import frame_motion_magnitude

def score_foreground_identity(sample: dict, feature_similarity: float|None=None, shape_change: float|None=None) -> dict:
    if feature_similarity is None and shape_change is None:
        if clean_has(sample, "id_mask"):
            return {
                "score": 1.0,
                "status": "ok",
                "backend": "physion_clean_gt_id_mask",
                "name": "R_fg",
                "metadata_backend": sample.get("clean_gt_backend_coverage"),
                "note": "Clean GT has simulator ID mask metadata; generated rollout still needs DINO/segmentation features.",
            }
        dino = sample.get("dino_feature_result") or {}
        if dino.get("available") and dino.get("backend") == "real":
            sim = dino.get("first_last_similarity")
            score = clamp01(0.5 + 0.5 * float(sim if sim is not None else 0.5))
            backend = "real_dino_id_mask" if sample.get("has_id_mask") or sample.get("id_path") else "real_dino_proxy_mask"
            return {
                "score": score,
                "status": "ok",
                "backend": backend,
                "name": "R_fg",
                "feature_similarity": sim,
                "feature_shape": dino.get("feature_shape"),
                "mask_backend": "id_mask" if backend == "real_dino_id_mask" else "central/global proxy mask",
                "feature_backend": dino,
                "note": "DINOv2-small forward is real; generated mask remains proxy when no ID mask exists.",
            }
        video=sample.get('candidate_video_path') or sample.get('video_path')
        motion=frame_motion_magnitude(video, max_frames=12)
        feature=first_last_feature_similarity(video)
        signature=video_feature_signature(video, max_frames=12)
        if sample.get('has_id_mask') or sample.get('id_path'):
            sim=feature.get('similarity')
            if sim is not None:
                score=clamp01(0.35 + 0.65*float(sim))
                return {'score':score,'status':'id_mask_plus_proxy_feature','name':'R_fg','motion_proxy':motion,'feature_proxy':feature,'temporal_signature':{k:v for k,v in signature.items() if k!='feature'},'backend':'DINOv2_hook_or_proxy'}
            return {'score':0.45,'status':'id_mask_available_feature_missing','name':'R_fg','motion_proxy':motion,'backend':'DINOv2_hook_or_proxy'}
        if motion.get('available'):
            sim=float(feature.get('similarity') or 0.5)
            motion_score=clamp01(1.0-float(motion.get('max_absdiff') or 0.0)*0.5)
            score=clamp01(0.55*sim+0.45*motion_score)
            return {'score':score,'status':'proxy_visual_feature_no_mask','name':'R_fg','motion_proxy':motion,'feature_proxy':feature,'temporal_signature':{k:v for k,v in signature.items() if k!='feature'},'backend':'DINOv2_hook_or_proxy'}
        return {'score':0.0,'status':'missing_video','name':'R_fg','todo':'use DINO/V-JEPA features plus mask area, bbox, contour stability'}
    score=1.0
    if feature_similarity is not None: score*=clamp01(feature_similarity)
    if shape_change is not None: score*=clamp01(1.0-shape_change)
    return {'score':score,'status':'ok','backend':'feature_shape_metric','name':'R_fg','feature_similarity':feature_similarity,'shape_change':shape_change}
