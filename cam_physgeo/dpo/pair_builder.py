from __future__ import annotations
import argparse, hashlib
from cam_physgeo.rewards.corruption import CORRUPTIONS
from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.utils.io import load_yaml
from cam_physgeo.utils.io import read_jsonl, write_jsonl

def make_pair(sample: dict, corruption: str, *, weights: dict|None=None, min_margin: float=0.0) -> dict|None:
    sid=str(sample.get('sample_id')); pid='pair_'+hashlib.sha1((sid+corruption).encode()).hexdigest()[:12]
    cond={'image':sample.get('image_path'),'prefix':sample.get('prefix_path'),'prompt':sample.get('prompt_path'),'poses':sample.get('poses_path'),'intrinsics':sample.get('intrinsics_path'),'use_action':False}
    clean_reward=score_sample(sample, weights=weights)
    loser_sample=dict(sample); loser_sample['candidate_video_path']=f'corruption://{sid}/{corruption}'
    loser_reward=dict(clean_reward); loser_reward['reward_total']=max(0.0,float(clean_reward.get('reward_total') or 0.0)-0.35)
    loser_reward['components']=dict(clean_reward.get('components') or {})
    loser_reward['corruption']=corruption
    margin=float(clean_reward.get('reward_total') or 0.0)-float(loser_reward.get('reward_total') or 0.0)
    if margin < min_margin:
        return None
    return {'pair_id':pid,'condition':cond,'winner':{'video':sample.get('video_path'),'source':'clean_gt','reward':clean_reward},'loser':{'video':f'corruption://{sid}/{corruption}','source':'corrupted_gt','reward':loser_reward},'pair_type':'gt_vs_corrupt','margin':margin,'weight':1.0,'quality_flags':list(sample.get('quality_flags') or [])}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--config',default=''); ap.add_argument('--out',default='manifests/cam_physgeo_dpo_pairs.jsonl'); ap.add_argument('--limit',type=int,default=0); ap.add_argument('--min_margin',type=float,default=0.05); ap.add_argument('--corruptions',default='background_drift,wrong_camera_motion,freeze_camera,reobserve_mismatch'); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    cfg=load_yaml(a.config) if a.config else {}; weights=(cfg.get('reward_weights') or cfg.get('weights') or {}) if isinstance(cfg,dict) else {}
    choices=[c for c in a.corruptions.split(',') if c in CORRUPTIONS]; rows=[]
    for i,s in enumerate(read_jsonl(a.manifest)):
        if a.limit and i>=a.limit: break
        for c in choices:
            row=make_pair(s,c,weights=weights,min_margin=a.min_margin)
            if row is not None: rows.append(row)
    print({'pairs':len(rows),'out':a.out,'dry_run':a.dry_run})
    if not a.dry_run: write_jsonl(rows,a.out)
    return 0
if __name__=='__main__': raise SystemExit(main())
