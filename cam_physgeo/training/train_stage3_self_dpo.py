from __future__ import annotations
import argparse
from cam_physgeo.training.train_utils import load_training_config, print_dry_run_plan

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--run',action='store_true'); ap.add_argument('--limit','--limit_pairs',dest='limit_pairs',type=int,default=0); ap.add_argument('--max_steps',type=int,default=0); ap.add_argument('--passk_report',default=''); a=ap.parse_args(argv)
    cfg=load_training_config(a.config); print_dry_run_plan('stage3_self_rollout_dpo', cfg, limit_pairs=a.limit_pairs, max_steps=a.max_steps, launch_gate='requires pass@K, quality, freeze, bg/cam thresholds before --run', passk_report=a.passk_report)
    if a.dry_run or not a.run:
        return 0
    raise RuntimeError('Stage3 self-rollout DPO is intentionally gated until anchored DPO produces acceptable pass@K rollouts.')
    return 0
if __name__=='__main__': raise SystemExit(main())
