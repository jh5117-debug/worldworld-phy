#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
export CUDA_VISIBLE_DEVICES=4
python3 -m cam_physgeo.dpo.dpo_v12b_winner_anchor_diag \
  --pair_manifest manifests/dpo_v12b_subsets/s8_winner_anchor_clean.jsonl \
  --scope L0_camera_r4 \
  --steps 5 \
  --gpu 0 \
  --output reports/dpo_objective_repair_v12b/winner_anchor_diag/per_pair_L0_camera_r4_5step.csv \
  --cache_root local_assets/dpo_objective_repair_v12b/winner_anchor_diag/cache_L0_camera_r4
