from __future__ import annotations
from cam_physgeo.rewards.geometry import score_background_rigid_consistency
from cam_physgeo.rewards.camera_following import score_camera_following
from cam_physgeo.rewards.foreground_identity import score_foreground_identity
from cam_physgeo.rewards.physics_event import score_physics_event
from cam_physgeo.rewards.reobserve import score_reobserve_consistency
from cam_physgeo.rewards.quality import score_quality
from cam_physgeo.rewards.freeze_penalty import score_freeze_penalty
from cam_physgeo.utils.geometry import clamp01
DEFAULT_WEIGHTS={'bg':1.0,'cam':1.0,'fg':1.0,'phys':1.0,'reobs':1.0,'quality':0.5,'freeze':1.0}
def score_sample(sample: dict, weights: dict|None=None) -> dict:
    w=dict(DEFAULT_WEIGHTS); w.update(weights or {})
    parts={'bg':score_background_rigid_consistency(sample),'cam':score_camera_following(sample),'fg':score_foreground_identity(sample),'phys':score_physics_event(sample),'reobs':score_reobserve_consistency(sample),'quality':score_quality(sample),'freeze':score_freeze_penalty(sample)}
    denom=sum(w[k] for k in ['bg','cam','fg','phys','reobs','quality'] if w[k]>0) or 1.0
    raw=sum(w[k]*parts[k].get('score',0.0) for k in ['bg','cam','fg','phys','reobs','quality'])/denom-w['freeze']*parts['freeze'].get('penalty',0.0)
    return {'sample_id':sample.get('sample_id'),'reward_total':clamp01(raw),'reward_raw':raw,'weights':w,'components':parts,'source':sample.get('source'),'template':sample.get('template'),'camera_motion':sample.get('camera_motion')}
