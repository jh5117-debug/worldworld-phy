from __future__ import annotations
import argparse
from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.utils.io import load_yaml, read_jsonl, write_jsonl

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--config',default=''); ap.add_argument('--out',default='manifests/cam_physgeo_reward_scores.jsonl'); ap.add_argument('--candidate_video_column',default=''); ap.add_argument('--limit',type=int,default=0); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    cfg=load_yaml(a.config) if a.config else {}; weights=(cfg.get('weights') or cfg.get('reward_weights') or {}) if isinstance(cfg,dict) else {}
    rows=[]
    for i,s in enumerate(read_jsonl(a.manifest)):
        if a.limit and i>=a.limit: break
        if a.candidate_video_column and s.get(a.candidate_video_column):
            s=dict(s); s['candidate_video_path']=s.get(a.candidate_video_column)
        rows.append(score_sample(s, weights=weights))
    print({'scored':len(rows),'out':a.out,'dry_run':a.dry_run})
    if not a.dry_run: write_jsonl(rows,a.out)
    return 0
if __name__=='__main__': raise SystemExit(main())
