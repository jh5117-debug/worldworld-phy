#!/usr/bin/env bash
set -euo pipefail
REPO=/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
cd "$REPO"
SESSION_LOG=reports/dpo_objective_search_v13b/S01_winner_detached_pref_low/checkpoint_eval/wait_eval.log
STATE=reports/dpo_objective_search_v13b/S01_winner_detached_pref_low/checkpoint_eval/wait_eval_state.jsonl
PY=/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python
MANIFEST=manifests/dpo_v13b_subsets/val_video_4.jsonl
CKPT=/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam
SCHEME=S01_winner_detached_pref_low
BASE_OUT=local_assets/dpo_objective_search_v13b/$SCHEME/rollouts
REPORT=reports/dpo_objective_search_v13b/$SCHEME/checkpoint_eval
mkdir -p "$BASE_OUT" "$REPORT"
log(){ echo "[$(date -Is)] $*" | tee -a "$SESSION_LOG"; }
gpu_busy_count(){ local gpu="$1"; timeout 10s nvidia-smi pmon -c 1 2>/dev/null | awk -v g="$gpu" '$1==g && $2!="-" {c++} END{print c+0}'; }
gpu_mem(){ local gpu="$1"; timeout 10s nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$gpu" 2>/dev/null | awk 'NR==1{print int($1)}'; }
pick_gpu(){ for gpu in 4 5; do mem=$(gpu_mem "$gpu" || echo 999999); busy=$(gpu_busy_count "$gpu" || echo 999); if [ "${mem:-999999}" -lt 1200 ] && [ "${busy:-999}" -eq 0 ]; then echo "$gpu"; return 0; fi; done; return 1; }
record_state(){ note="$1"; g4m=$(gpu_mem 4 || echo -1); g5m=$(gpu_mem 5 || echo -1); g4b=$(gpu_busy_count 4 || echo -1); g5b=$(gpu_busy_count 5 || echo -1); printf '{"timestamp":"%s","note":"%s","gpu4_mem_mb":%s,"gpu5_mem_mb":%s,"gpu4_busy_pids":%s,"gpu5_busy_pids":%s}\n' "$(date -Is)" "$note" "$g4m" "$g5m" "$g4b" "$g5b" >> "$STATE"; }
run_eval(){ step="$1"; gpu="$2"; adapter="$3"; out="$BASE_OUT/step${step}"; logf="$REPORT/step${step}_rollout.log"; [ -d "$adapter" ] || { log "missing adapter dir for step${step}: $adapter"; return 3; }; log "starting S01 step${step} checkpoint eval on physical GPU${gpu}"; CUDA_VISIBLE_DEVICES="$gpu" TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True "$PY" -m cam_physgeo.eval.run_fast_adapter_inference --manifest "$MANIFEST" --out "$out" --model_label "S01_step${step}" --ckpt_dir "$CKPT" --max_samples 4 --per_template 4 --frame_num 81 --size '832*480' --height 480 --width 832 --seed 123 --skip_existing --adapter_dir "$adapter" > "$logf" 2>&1; n=$(find "$out" -name '*.mp4' 2>/dev/null | wc -l); log "finished step${step} mp4_count=$n out=$out log=$logf"; [ "$n" -gt 0 ]; }
log "v13b S01 checkpoint eval waiter started; allowed physical GPUs: 4,5 only; forbidden: 0,1,2,3,6,7"
record_state start
while true; do gpu=$(pick_gpu || true); if [ -n "${gpu:-}" ]; then log "selected physical GPU${gpu} for eval"; break; fi; record_state wait_gpu45_busy; sleep 60; done
run_eval 050 "$gpu" "local_assets/dpo_objective_search_v13b/$SCHEME/adapter_dirs/step050_fast_stageA_high_noise_adapter"
record_state after_step050
run_eval 000 "$gpu" "local_assets/dpo_objective_search_v13b/$SCHEME/adapter_dirs/step000_fast_stageA_high_noise_adapter"
record_state done
log "v13b S01 checkpoint eval waiter completed"
