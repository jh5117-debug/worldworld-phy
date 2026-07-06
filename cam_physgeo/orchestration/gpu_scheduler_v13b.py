from __future__ import annotations
import argparse, json, subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
ALLOWED=[4,5]; FORBIDDEN=[0,1,2,3,6,7]
SCHEMES=['S01_winner_detached_pref_low','S02_winner_detached_pref_lower_lr','S04_no_lose_gap_normalized_win_only','S05_normalized_clipped_loser_alpha005','S07_linear_winner_detached','S08_delayed_loser_gradient_tiny','S09_local_time_mask_winner_detached','S06_normalized_clipped_loser_alpha010','S10_lora_camera_temporal_winner_detached','S03_winner_detached_pref_earlystop_best']
def now(): return datetime.now().astimezone().isoformat(timespec='seconds')
def query_gpus() -> dict[int,dict[str,Any]]:
    cmd = [
        'timeout', '-k', '2s', '8s',
        'nvidia-smi',
        '--query-gpu=index,memory.used,memory.total,utilization.gpu',
        '--format=csv,noheader,nounits',
    ]
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
    except Exception as exc:
        return {'error': {'error': repr(exc), 'source': 'python_subprocess_timeout'}}  # type: ignore
    if proc.returncode != 0:
        return {'error': {'error': proc.stderr.strip() or proc.stdout.strip(), 'returncode': proc.returncode, 'source': 'nvidia_smi_timeout_or_error'}}  # type: ignore
    rows = {}
    for line in proc.stdout.splitlines():
        parts = [part.strip() for part in line.split(',')]
        if len(parts) >= 4:
            idx = int(parts[0])
            rows[idx] = {
                'index': idx,
                'memory_used_mb': int(parts[1]),
                'memory_total_mb': int(parts[2]),
                'utilization_percent': int(parts[3]),
            }
    return rows
def idle_allowed_gpus(status, mem_threshold=1000, util_threshold=10):
    return [g for g in ALLOWED if status.get(g) and int(status[g].get('memory_used_mb',999999))<=mem_threshold and int(status[g].get('utilization_percent',999))<=util_threshold]
def write_json(path,data): Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def append_jsonl(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open('a',encoding='utf-8') as f: f.write(json.dumps(data,sort_keys=True)+'\n')
def build_command(scheme, physical_gpu, steps): return f'CUDA_VISIBLE_DEVICES={physical_gpu} PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python3 -m cam_physgeo.dpo.dpo_objective_search_v13b --scheme_id {scheme} --gpu 0 --steps {steps} --report_root reports/dpo_objective_search_v13b --output_root local_assets/dpo_objective_search_v13b'
def run_once(args):
    report=Path(args.report_root); report.mkdir(parents=True,exist_ok=True); status=query_gpus(); idle=idle_allowed_gpus(status,int(args.idle_memory_threshold_mb),int(args.idle_util_threshold_percent)) if 'error' not in status else []
    state={'timestamp':now(),'allowed_gpus':ALLOWED,'forbidden_gpus':FORBIDDEN,'gpu_status':status,'idle_allowed_gpus':idle,'jobs':[]}
    if not idle:
        state['decision']='GPU4_5_BLOCKED'; write_json(args.state,state); append_jsonl(args.heartbeat,{'timestamp':now(),'decision':'GPU4_5_BLOCKED','gpu_status':status}); (report/'final_summary.md').write_text('# v13b Scheduler Summary\n\nDecision: `GPU4_5_BLOCKED`\n\nGPU4/5 were not idle; no training launched.\n'); print(json.dumps(state,indent=2,sort_keys=True)); return state
    launched=[]
    for gpu, scheme in zip(idle[:int(args.max_parallel_jobs)], SCHEMES):
        cmd=build_command(scheme,gpu,int(args.steps_per_scheme)); status_job='DRY_RUN'
        if not args.dry_run:
            session=f'dpo_v13b_{scheme}_gpu{gpu}'[:80]; subprocess.run(['tmux','new','-d','-s',session,f'cd {Path.cwd()} && {cmd}'],check=True); status_job='RUNNING'
        launched.append({'job_id':scheme,'assigned_gpus':[gpu],'command':cmd,'status':status_job})
    state['decision']='LAUNCHED' if launched else 'NO_JOB'; state['jobs']=launched; write_json(args.state,state); append_jsonl(args.heartbeat,{'timestamp':now(),'decision':state['decision'],'jobs':launched,'gpu_status':status}); print(json.dumps(state,indent=2,sort_keys=True)); return state
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--config',default='configs/cam_physgeo/dpo_objective_search_v13b.yaml'); p.add_argument('--state',default='reports/dpo_objective_search_v13b/scheduler_state.json'); p.add_argument('--heartbeat',default='reports/dpo_objective_search_v13b/heartbeat.jsonl'); p.add_argument('--report_root',default='reports/dpo_objective_search_v13b'); p.add_argument('--idle_memory_threshold_mb',type=int,default=1000); p.add_argument('--idle_util_threshold_percent',type=int,default=10); p.add_argument('--max_parallel_jobs',type=int,default=2); p.add_argument('--steps_per_scheme',type=int,default=200); p.add_argument('--dry_run',action='store_true'); run_once(p.parse_args(argv))
if __name__=='__main__': main()
