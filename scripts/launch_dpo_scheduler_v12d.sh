#!/usr/bin/env bash
set -euo pipefail
REPO=/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
SESSION=dpo_gpu_scheduler_v12d
cd "$REPO"
mkdir -p reports/dpo_gpu_scheduler_v12d
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session $SESSION already exists"
  exit 0
fi
tmux new -d -s "$SESSION" "cd '$REPO' && PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python3 -m cam_physgeo.orchestration.gpu_scheduler_v12d --config configs/cam_physgeo/dpo_scheduler_v12d.yaml --state reports/dpo_gpu_scheduler_v12d/scheduler_state.json --heartbeat reports/dpo_gpu_scheduler_v12d/heartbeat.jsonl --log reports/dpo_gpu_scheduler_v12d/scheduler.log"
echo "$SESSION"
