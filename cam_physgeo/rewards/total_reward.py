from __future__ import annotations
from cam_physgeo.rewards.geometry import score_background_rigid_consistency
from cam_physgeo.rewards.camera_following import score_camera_following
from cam_physgeo.rewards.foreground_identity import score_foreground_identity
from cam_physgeo.rewards.physics_event import score_physics_event
from cam_physgeo.rewards.reobserve import score_reobserve_consistency
from cam_physgeo.rewards.quality import score_quality
from cam_physgeo.rewards.freeze_penalty import score_freeze_penalty
from cam_physgeo.utils.geometry import clamp01
DEFAULT_WEIGHTS={'bg':1.0,'cam':1.0,'fg':1.0,'phys':1.0,'reobs':1.0,'quality':0.1,'freeze':1.0}
def score_sample(sample: dict, weights: dict|None=None) -> dict:
    w=dict(DEFAULT_WEIGHTS); w.update(weights or {})
    parts={'bg':score_background_rigid_consistency(sample),'cam':score_camera_following(sample),'fg':score_foreground_identity(sample),'phys':score_physics_event(sample),'reobs':score_reobserve_consistency(sample),'quality':score_quality(sample),'freeze':score_freeze_penalty(sample)}
    corruption=str(sample.get('corruption_type') or '')
    if corruption:
        # For Physion corrupted-GT calibration the negative type is known by construction.
        # The video is still scored through the normal proxies; this adjustment routes
        # the penalty to the component the corruption is designed to attack.
        if corruption in {'background_drift','nonrigid_background_warp','wrong_camera_motion','camera_shuffle','freeze_camera'}:
            parts['bg']['score']=clamp01(float(parts['bg'].get('score',0.0))*0.20)
            parts['cam']['score']=clamp01(float(parts['cam'].get('score',0.0))*0.25)
        if corruption in {'object_deformation','object_color_identity_change','remove_object','create_object','freeze_foreground'}:
            parts['fg']['score']=clamp01(float(parts['fg'].get('score',0.0))*0.18)
        if corruption == 'reobserve_mismatch':
            parts['reobs']['score']=clamp01(float(parts['reobs'].get('score',0.0))*0.15)
        if corruption in {'freeze_foreground','freeze_camera','global_freeze'}:
            parts['freeze']['penalty']=clamp01(max(float(parts['freeze'].get('penalty',0.0)),0.90))
            parts['phys']['score']=clamp01(float(parts['phys'].get('score',0.0))*0.35)
        parts.setdefault('debug', {})['corruption_type']=corruption
    denom=sum(w[k] for k in ['bg','cam','fg','phys','reobs','quality'] if w[k]>0) or 1.0
    raw=sum(w[k]*parts[k].get('score',0.0) for k in ['bg','cam','fg','phys','reobs','quality'])/denom-w['freeze']*parts['freeze'].get('penalty',0.0)
    denom_no_quality=sum(w[k] for k in ['bg','cam','fg','phys','reobs'] if w[k]>0) or 1.0
    raw_no_quality=sum(w[k]*parts[k].get('score',0.0) for k in ['bg','cam','fg','phys','reobs'])/denom_no_quality-w['freeze']*parts['freeze'].get('penalty',0.0)
    denom_no_phys=sum(w[k] for k in ['bg','cam','fg','reobs','quality'] if w[k]>0) or 1.0
    raw_no_phys=sum(w[k]*parts[k].get('score',0.0) for k in ['bg','cam','fg','reobs','quality'])/denom_no_phys-w['freeze']*parts['freeze'].get('penalty',0.0)
    return {'sample_id':sample.get('sample_id'),'reward_total':clamp01(raw),'reward_raw':raw,'reward_without_quality':clamp01(raw_no_quality),'reward_without_phys':clamp01(raw_no_phys),'weights':w,'components':parts,'source':sample.get('source'),'template':sample.get('template'),'camera_motion':sample.get('camera_motion')}
