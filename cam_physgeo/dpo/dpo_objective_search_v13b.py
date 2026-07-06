from __future__ import annotations
import argparse, json, os
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from cam_physgeo.dpo.dpo_v12c_probe_setup import find_warm_start
from cam_physgeo.dpo.gap_metrics_v13b import decide_gap_health, enrich_training_csv, summarize_gap_csv
from cam_physgeo.dpo.pair_cache_objective_runner import run_objective
DEFAULT_CACHE_ROOT='local_assets/dpo_objective_repair_v12b/winner_curriculum/cache_s_pass4'
DEFAULT_PAIR_SUBSET='local_assets/dpo_objective_repair_v12b/winner_curriculum/cache_s_pass4/cache_index.jsonl'
SCHEMES={'S01':{'objective':'winner_detached_preference','scope':'L0_camera_r4','beta':0.05,'lambda_pref':0.005,'lr':1e-6,'steps':200},'S02':{'objective':'winner_detached_preference','scope':'L0_camera_r4','beta':0.05,'lambda_pref':0.005,'lr':5e-7,'steps':200},'S03':{'objective':'winner_detached_preference','scope':'L0_camera_r4','beta':0.05,'lambda_pref':0.005,'lr':1e-6,'steps':200,'earlystop_best':True},'S04':{'objective':'no_lose_gap_normalized_win_only','scope':'L0_camera_r4','beta':0.05,'lambda_pref':0.0,'lambda_win':0.5,'lr':1e-6,'steps':200},'S05':{'objective':'normalized_clipped_loser','scope':'L0_camera_r4','beta':0.1,'alpha_l':0.05,'lambda_anchor':1.0,'lambda_win':0.5,'lr':1e-6,'steps':200},'S06':{'objective':'normalized_clipped_loser','scope':'L0_camera_r4','beta':0.1,'alpha_l':0.10,'lambda_anchor':1.0,'lambda_win':0.5,'lr':1e-6,'steps':200},'S07':{'objective':'linear_winner_detached','scope':'L0_camera_r4','beta':0.05,'lambda_winner_anchor':1.0,'lr':1e-6,'steps':200},'S08':{'objective':'tiny_loser_gradient_preference','scope':'L0_camera_r4','beta':0.05,'lambda_pref':0.005,'max_lambda_loser':0.02,'lr':1e-6,'steps':200},'S09':{'objective':'winner_detached_preference','scope':'L0_camera_r4','beta':0.05,'lambda_pref':0.005,'lr':1e-6,'steps':200,'mask_mode':'LOCAL_TIME_ONLY_OR_SPATIAL'},'S10':{'objective':'winner_detached_preference','scope':'L2_camera_temporal_r4','beta':0.05,'lambda_pref':0.005,'lr':1e-6,'steps':100}}
def allowed_cuda_visible_devices() -> bool:
    cvd=os.environ.get('CUDA_VISIBLE_DEVICES',''); return cvd in {'4','5'} or cvd.startswith('4,5') or cvd.startswith('5,4')
def scheme_config(scheme_id: str) -> dict[str, Any]:
    key=scheme_id.split('_',1)[0]
    if key not in SCHEMES: raise KeyError(f'unknown scheme_id={scheme_id}')
    cfg=dict(SCHEMES[key]); cfg['scheme_id']=scheme_id; return cfg
def run_scheme(args: argparse.Namespace) -> dict[str, Any]:
    if not args.dry_run and not allowed_cuda_visible_devices(): raise RuntimeError(f'CUDA_VISIBLE_DEVICES must be physical GPU4 or GPU5 for v13b, got {os.environ.get("CUDA_VISIBLE_DEVICES","")}')
    cfg=scheme_config(args.scheme_id); report_root=Path(args.report_root)/args.scheme_id; output_root=Path(args.output_root)/args.scheme_id; report_root.mkdir(parents=True, exist_ok=True); output_root.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        summary={'scheme_id':args.scheme_id,'status':'DRY_RUN','config':cfg}; (report_root/'training_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps(summary,indent=2,sort_keys=True)); return summary
    init=args.init_lora_state
    if not init:
        warm=find_warm_start(); init=str(warm.get('checkpoint_path') or '') if warm.get('warm_start_available') else ''
    steps=int(args.steps or cfg.get('steps',200)); out_csv=report_root/f'{args.scheme_id}_{steps}step.csv'
    ns=SimpleNamespace(cache_root=args.cache_root,pair_subset=args.pair_subset,objective=cfg['objective'],steps=steps,gpu=int(args.gpu),output=str(out_csv),scope=cfg.get('scope','L0_camera_r4'),config=args.config,height=int(args.height),width=int(args.width),used_window_frames=int(args.used_window_frames),lr=float(args.lr if args.lr is not None else cfg.get('lr',1e-6)),beta=float(cfg.get('beta',0.05)),u_clip=float(args.u_clip),lambda_winner_anchor=float(cfg.get('lambda_winner_anchor',1.0)),lambda_pref=float(cfg.get('lambda_pref',0.005)),max_lambda_loser=float(cfg.get('max_lambda_loser',0.0)),alpha_l=float(cfg.get('alpha_l',0.05)),clip_loser=float(args.clip_loser),lambda_win=float(cfg.get('lambda_win',0.5)),lambda_anchor=float(cfg.get('lambda_anchor',1.0)),init_lora_state=init,checkpoint_root=str(output_root/'checkpoints'),checkpoint_steps=args.checkpoint_steps,gradient_checkpointing=True)
    raw=run_objective(ns); enriched=enrich_training_csv(out_csv, report_root/f'{args.scheme_id}_{steps}step_gap_enriched.csv', clip_loser=float(args.clip_loser)); gaps=summarize_gap_csv(enriched); decision=decide_gap_health(gaps)
    summary={**raw,'scheme_id':args.scheme_id,'scheme_config':cfg,'gap_summary':gaps,'training_signal_decision':decision,'gap_enriched_csv':str(enriched),'init_lora_state':init}
    (report_root/'training_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    (report_root/'training_summary.md').write_text(f"# v13b {args.scheme_id} Summary\n\n- Objective: `{cfg['objective']}`\n- Scope: `{cfg.get('scope')}`\n- Steps requested: `{steps}`\n- Raw status: `{raw.get('status')}`\n- Training signal decision: `{decision}`\n- Mean win_gap: `{gaps.get('mean_win_gap')}`\n- Mean lose_gap: `{gaps.get('mean_lose_gap')}`\n- Mean winner_improvement_post: `{gaps.get('mean_winner_improvement_post')}`\n- Final winner_improvement_post: `{gaps.get('final_winner_improvement_post')}`\n- Mean winner_contribution_ratio: `{gaps.get('mean_winner_contribution_ratio')}`\n- Mean loser_dominance: `{gaps.get('mean_loser_dominance')}`\n- Gap CSV: `{enriched}`\n\nVideo/metric validation is still required before any scheme can be called a valid DPO recipe.\n")
    print(json.dumps(summary,indent=2,sort_keys=True)); return summary
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--scheme_id',required=True); p.add_argument('--cache_root',default=DEFAULT_CACHE_ROOT); p.add_argument('--pair_subset',default=DEFAULT_PAIR_SUBSET); p.add_argument('--gpu',type=int,default=0); p.add_argument('--steps',type=int,default=0); p.add_argument('--output_root',default='local_assets/dpo_objective_search_v13b'); p.add_argument('--report_root',default='reports/dpo_objective_search_v13b'); p.add_argument('--init_lora_state',default=''); p.add_argument('--config',default='configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml'); p.add_argument('--height',type=int,default=480); p.add_argument('--width',type=int,default=832); p.add_argument('--used_window_frames',type=int,default=49); p.add_argument('--lr',type=float,default=None); p.add_argument('--u_clip',type=float,default=1.0); p.add_argument('--clip_loser',type=float,default=1.0); p.add_argument('--checkpoint_steps',default='0,50,100,200'); p.add_argument('--dry_run',action='store_true'); run_scheme(p.parse_args(argv))
if __name__=='__main__': main()
