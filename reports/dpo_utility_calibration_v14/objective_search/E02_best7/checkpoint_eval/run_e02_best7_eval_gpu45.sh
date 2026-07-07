#!/usr/bin/env bash
set -uo pipefail
REPO=/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
cd "$REPO"
PY=/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python
MANIFEST=manifests/dpo_v12b_subsets/val_video_4.jsonl
CKPT=/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam
SCHEME=E02_best7
BASE_OUT=local_assets/dpo_utility_calibration_v14/objective_search/$SCHEME/rollouts
REPORT=reports/dpo_utility_calibration_v14/objective_search/$SCHEME/checkpoint_eval
METRICS=reports/dpo_utility_calibration_v14/objective_search/$SCHEME/metrics
mkdir -p "$BASE_OUT" "$REPORT" "$METRICS" "$REPORT/contact_sheets"
LOG="$REPORT/eval_gpu45.log"
STATE="$REPORT/eval_gpu45_state.jsonl"
log(){ echo "[$(date -Is)] $*" | tee -a "$LOG"; }
gpu_busy_count(){ local gpu="$1"; timeout 10s nvidia-smi pmon -c 1 2>/dev/null | awk -v g="$gpu" '$1==g && $2!="-" {c++} END{print c+0}'; }
gpu_mem(){ local gpu="$1"; timeout 10s nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$gpu" 2>/dev/null | awk 'NR==1{print int($1)}'; }
pick_gpu(){ for gpu in 4 5; do mem=$(gpu_mem "$gpu" || echo 999999); busy=$(gpu_busy_count "$gpu" || echo 999); if [ "${mem:-999999}" -lt 1200 ] && [ "${busy:-999}" -eq 0 ]; then echo "$gpu"; return 0; fi; done; return 1; }
record(){ note="$1"; printf '{"timestamp":"%s","note":"%s","gpu4_mem_mb":%s,"gpu5_mem_mb":%s,"gpu4_busy":%s,"gpu5_busy":%s}\n' "$(date -Is)" "$note" "$(gpu_mem 4 || echo -1)" "$(gpu_mem 5 || echo -1)" "$(gpu_busy_count 4 || echo -1)" "$(gpu_busy_count 5 || echo -1)" >> "$STATE"; }
wait_for_gpu(){ while true; do g=$(pick_gpu || true); if [ -n "${g:-}" ]; then echo "$g"; return 0; fi; record wait_gpu45_busy; sleep 60; done; }
run_step(){
  local step="$1"; local state="$2"; local gpu
  gpu=$(wait_for_gpu)
  local out="$BASE_OUT/step${step}"
  local logf="$REPORT/step${step}_rollout.log"
  log "starting E02_best7 step${step} eval on physical GPU${gpu}; lora_state=${state}"
  record "start_step${step}_gpu${gpu}"
  CUDA_VISIBLE_DEVICES="$gpu" TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    "$PY" -m cam_physgeo.eval.run_fast_adapter_inference \
      --manifest "$MANIFEST" \
      --out "$out" \
      --model_label "E02_best7_step${step}" \
      --ckpt_dir "$CKPT" \
      --max_samples 4 \
      --per_template 4 \
      --frame_num 81 \
      --size '832*480' \
      --height 480 \
      --width 832 \
      --seed 123 \
      --skip_existing \
      --lora_state "$state" \
      --lora_rank 4 \
      --lora_alpha 4 \
      --lora_target_groups camera_conditioning \
      > "$logf" 2>&1
  code=$?
  n=$(find "$out" -name '*.mp4' 2>/dev/null | wc -l)
  log "finished step${step} exit=${code} mp4_count=${n} out=${out} log=${logf}"
  record "finish_step${step}_exit${code}_mp4${n}"
  [ "$code" -eq 0 ] && [ "$n" -ge 4 ]
}
log "E02_best7 checkpoint eval start; allowed physical GPUs: 4,5 only"
record start
run_step 000 local_assets/dpo_utility_calibration_v14/objective_search/E02_best7/checkpoints/calibrated_winner_detached_log_L0_camera_r4_step000_lora_state.pt || exit 1
run_step 005 local_assets/dpo_utility_calibration_v14/objective_search/E02_best7/checkpoints/calibrated_winner_detached_log_L0_camera_r4_step005_lora_state.pt || exit 1
run_step 007 local_assets/dpo_utility_calibration_v14/objective_search/E02_best7/checkpoints/calibrated_winner_detached_log_L0_camera_r4_step007_lora_state.pt || exit 1
log "rollouts complete; building combined manifest, metrics input, and contact sheets"
"$PY" - <<'PY'
import csv, json
from pathlib import Path
import cv2
import numpy as np
REPO=Path('.')
SCHEME='E02_best7'
base=Path('local_assets/dpo_utility_calibration_v14/objective_search')/SCHEME/'rollouts'
report=Path('reports/dpo_utility_calibration_v14/objective_search')/SCHEME/'checkpoint_eval'
metrics=Path('reports/dpo_utility_calibration_v14/objective_search')/SCHEME/'metrics'
contact=report/'contact_sheets'
contact.mkdir(parents=True, exist_ok=True); metrics.mkdir(parents=True, exist_ok=True)
all_rows=[]
for step in ['000','005','007']:
    p=base/f'step{step}'/'generated_manifest.csv'
    if not p.exists():
        continue
    with p.open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row=dict(row); row['checkpoint']=f'step{step}'; row['scheme_id']=SCHEME
            row['reference_video_path']=row.get('source_video','')
            row['prediction_video_path']=row.get('generated_video','')
            all_rows.append(row)
keys=sorted({k for r in all_rows for k in r})
for out in [report/'generated_manifest.csv', metrics/'metrics_input.csv']:
    with out.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(all_rows)

def read_frames(path, n=6):
    cap=cv2.VideoCapture(str(path)); frames=[]
    total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    idxs=np.linspace(0, max(total-1,0), n).round().astype(int).tolist() if total else list(range(n))
    want=set(idxs); i=0
    while True:
        ok, frame=cap.read()
        if not ok: break
        if i in want:
            frame=cv2.resize(frame, (240,135), interpolation=cv2.INTER_AREA)
            frames.append(frame)
        i+=1
    cap.release()
    while len(frames)<n:
        frames.append(np.zeros((135,240,3), dtype=np.uint8))
    return frames[:n]
manifest=[]
for row in all_rows:
    ref=row.get('reference_video_path') or ''
    pred=row.get('prediction_video_path') or ''
    if not ref or not pred: continue
    ref_frames=read_frames(ref); pred_frames=read_frames(pred)
    canvas=np.zeros((270, 240*6, 3), dtype=np.uint8)
    for i,fr in enumerate(ref_frames): canvas[0:135, i*240:(i+1)*240]=fr
    for i,fr in enumerate(pred_frames): canvas[135:270, i*240:(i+1)*240]=fr
    name=f"{row.get('checkpoint','step')}_{row.get('sample_id','sample')}_{SCHEME}.jpg".replace('/','_')
    out=contact/name
    cv2.imwrite(str(out), canvas)
    manifest.append({
        'sample_id': row.get('sample_id',''), 'checkpoint': row.get('checkpoint',''), 'scheme_id': SCHEME,
        'contact_sheet_path': str(out), 'reference_video_path': ref, 'prediction_video_path': pred,
        'reviewed': 'false', 'written_reason': '', 'status': 'PENDING_CODEX_VISUAL_AUDIT'
    })
with (contact/'contact_sheet_manifest.csv').open('w', newline='', encoding='utf-8') as f:
    keys=sorted({k for r in manifest for k in r}) if manifest else ['sample_id','checkpoint','contact_sheet_path']
    w=csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(manifest)
summary={
    'scheme_id': SCHEME,
    'generated_rows': len(all_rows),
    'contact_sheets': len(manifest),
    'status': 'ROLLOUTS_DONE_AWAITING_METRICS_AND_CODEX_VISUAL_AUDIT'
}
(report/'checkpoint_eval_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n', encoding='utf-8')
(report/'checkpoint_eval_summary.md').write_text('# E02_best7 Checkpoint Eval Summary\n\n'
    f"- Generated rows: `{len(all_rows)}`\n"
    f"- Contact sheets: `{len(manifest)}`\n"
    '- Codex visual audit: `PENDING`\n'
    '- Metrics: `PENDING`\n', encoding='utf-8')
print(json.dumps(summary, indent=2, sort_keys=True))
PY
log "running checkpoint metrics"
CUDA_VISIBLE_DEVICES=4 "$PY" -m cam_physgeo.eval.eval_checkpoint_videos \
  --manifest "$METRICS/metrics_input.csv" \
  --out_dir "$METRICS" \
  --compute_lpips \
  --lpips_max_frames 8 \
  --lpips_device cpu \
  > "$METRICS/eval_checkpoint_videos.log" 2>&1 || true
if [ -f "$METRICS/per_sample_metrics.csv" ]; then cp "$METRICS/per_sample_metrics.csv" "$METRICS/psnr_ssim_lpips.csv"; fi
log "E02_best7 checkpoint eval script completed; Codex visual audit still required"
record done
