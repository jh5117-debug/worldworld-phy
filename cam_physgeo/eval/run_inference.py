from __future__ import annotations
import argparse
from cam_physgeo.training.model_loading import check_legacy_lingbot_import, resolve_model_paths
from cam_physgeo.utils.io import load_yaml

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--out',default='outputs/cam_physgeo_rollouts'); ap.add_argument('--model_type',default='fast',choices=['base','fast']); ap.add_argument('--sample_steps',type=int,default=8); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    paths=resolve_model_paths(load_yaml('configs/cam_physgeo/paths.yaml')); model_path=paths['lingbot_fast' if a.model_type=='fast' else 'lingbot_base']; import_check=check_legacy_lingbot_import(paths['lingbot_code'])
    print({'inference_out':a.out,'manifest':a.manifest,'model_type':a.model_type,'model_path':model_path,'lingbot_code':paths['lingbot_code'],'legacy_import':import_check,'sample_steps':a.sample_steps,'control_type':'cam','use_action':False,'dry_run':a.dry_run})
    if not a.dry_run:
        raise RuntimeError('Use the legacy eval_batch/LingBot fast runtime with the printed paths; long inference launch is intentionally explicit.')
    return 0
if __name__=='__main__': raise SystemExit(main())
