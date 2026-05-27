from __future__ import annotations
import argparse
from pathlib import Path
from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.utils.io import load_yaml, read_jsonl, write_jsonl

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--config',default=''); ap.add_argument('--out',default='local_assets/reports/smoke/reward_scores.jsonl'); ap.add_argument('--source',default='',choices=['','physion_official','physion_movingcam']); ap.add_argument('--candidate_video_column',default=''); ap.add_argument('--limit',type=int,default=0); ap.add_argument('--save_debug_vis',action='store_true'); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    cfg=load_yaml(a.config) if a.config else {}; weights=(cfg.get('weights') or cfg.get('reward_weights') or {}) if isinstance(cfg,dict) else {}
    rows=[]
    seen=0
    for s in read_jsonl(a.manifest):
        if a.source and s.get('source') != a.source: continue
        if a.limit and seen>=a.limit: break
        if a.candidate_video_column and s.get(a.candidate_video_column):
            s=dict(s); s['candidate_video_path']=s.get(a.candidate_video_column)
        rows.append(score_sample(s, weights=weights))
        seen+=1
    print({'scored':len(rows),'out':a.out,'source':a.source,'save_debug_vis':a.save_debug_vis,'dry_run':a.dry_run})
    if not a.dry_run:
        write_jsonl(rows,a.out)
        if a.save_debug_vis:
            Path(a.out).with_suffix('.debug.md').write_text('# Reward Debug Smoke\n\nDebug visualization hooks are enabled; flow/depth residual image export is pending backend availability.\n', encoding='utf-8')
    return 0
if __name__=='__main__': raise SystemExit(main())
