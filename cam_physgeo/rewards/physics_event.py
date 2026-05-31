from __future__ import annotations
from cam_physgeo.rewards.metadata_backend import clean_has
from cam_physgeo.utils.geometry import clamp01
from cam_physgeo.utils.video import frame_motion_magnitude
EVENT_RULES={'drop':['downward motion','no floating','no ground penetration','no disappearance'],'collision':['post-contact response','no object fusion','no penetration'],'roll':['continuous center trajectory','no teleport','no unexplained jump'],'containment':['stable object-container relation','no unexplained escape'],'support':['supported objects remain stable','unsupported objects fall']}
def score_physics_event(sample: dict, rule_pass_rate: float|None=None) -> dict:
    template=str(sample.get('template') or 'unknown')
    rules=EVENT_RULES.get(template, [])
    if rule_pass_rate is None:
        if clean_has(sample, "object_state"):
            return {
                "score": 1.0,
                "status": "ok",
                "backend": "physion_clean_gt_object_state",
                "name": "R_phys",
                "template": template,
                "rules": rules,
                "metadata_backend": sample.get("clean_gt_backend_coverage"),
            }
        motion=frame_motion_magnitude(sample.get('candidate_video_path') or sample.get('video_path'), max_frames=16)
        if not rules:
            return {'score':0.5 if motion.get('available') else 0.0,'status':'unknown_template','name':'R_phys','template':template,'rules':rules,'motion_proxy':motion}
        if motion.get('available'):
            mean=float(motion.get('mean_absdiff') or 0.0); maxv=float(motion.get('max_absdiff') or 0.0)
            continuity=1.0-clamp01(max(0.0, maxv-mean*4.0)/0.25)
            activity=clamp01(mean/0.015) if template in {'drop','collision','roll'} else clamp01(1.0-mean/0.20)
            return {'score':clamp01(0.5*continuity+0.5*activity),'status':'motion_proxy','name':'R_phys','template':template,'rules':rules,'motion_proxy':motion}
        return {'score':0.0,'status':'missing_video','name':'R_phys','template':template,'rules':rules,'todo':'fill with mask/track based event checks'}
    return {'score':max(0.0,min(1.0,float(rule_pass_rate))),'status':'ok','backend':'event_rule_metric','name':'R_phys','template':template,'rules':rules}
