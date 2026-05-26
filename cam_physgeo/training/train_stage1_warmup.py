from __future__ import annotations
import argparse, os, subprocess, sys
from cam_physgeo.training.model_loading import check_legacy_lingbot_import, resolve_model_paths
from cam_physgeo.training.train_utils import load_training_config, print_dry_run_plan

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--run',action='store_true'); ap.add_argument('--limit_samples',type=int,default=0); ap.add_argument('--max_steps',type=int,default=0); ap.add_argument('--legacy_config',default='configs/train_stage1_physinone_cam.yaml'); ap.add_argument('--branch_mode',default='low',choices=['sequence','low','high']); a=ap.parse_args(argv)
    cfg=load_training_config(a.config); paths=resolve_model_paths(load_training_config('configs/cam_physgeo/paths.yaml')); import_check=check_legacy_lingbot_import(paths['lingbot_code'])
    command=[sys.executable,'-m','physical_consistency.stages.stage1_physinone_cam.runner','--config',a.legacy_config,'--control_type','cam','--base_model_dir',paths['lingbot_base'],'--lingbot_code_dir',paths['lingbot_code'],'--branch_mode',a.branch_mode]
    if a.max_steps:
        os.environ['PC_STAGE1_MAX_STEPS']=str(a.max_steps)
    print_dry_run_plan('stage1_support_warmup', cfg, command=command, limit_samples=a.limit_samples, max_steps=a.max_steps, legacy_import=import_check, action_conditioning='disabled: control_type=cam; action.npy dummy only for compatibility')
    if a.dry_run or not a.run:
        return 0
    if not import_check.get('import_ok'):
        raise RuntimeError(f"LingBot import failed: {import_check}")
    return subprocess.call(command)
if __name__=='__main__': raise SystemExit(main())
