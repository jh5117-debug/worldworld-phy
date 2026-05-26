from __future__ import annotations
import argparse
from cam_physgeo.training.train_utils import load_training_config, print_dry_run_plan

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--run',action='store_true'); a=ap.parse_args(argv)
    cfg=load_training_config(a.config); print_dry_run_plan('trd_auxiliary', cfg)
    if not a.dry_run and a.run: raise RuntimeError('Long training is not implemented in first-stage skeleton.')
    return 0
if __name__=='__main__': raise SystemExit(main())
