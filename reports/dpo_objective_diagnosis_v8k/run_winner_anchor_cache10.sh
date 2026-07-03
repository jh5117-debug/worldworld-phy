#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
CUDA_VISIBLE_DEVICES=7 python3 -m cam_physgeo.dpo.winner_anchor_only_runner \
  --cache_root local_assets/dpo_objective_cache_v8j/gt_c_10_window49 \
  --num_pairs 10 \
  --steps 20 \
  --gpu 0 \
  --mode cache_only_policy_train \
  --output reports/dpo_objective_diagnosis_v8k/winner_anchor_cache10_20step.csv \
  > reports/dpo_objective_diagnosis_v8k/winner_anchor_cache10_20step.stdout.log 2>&1
