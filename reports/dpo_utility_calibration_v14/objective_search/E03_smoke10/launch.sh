#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
export CUDA_VISIBLE_DEVICES=5
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 -m cam_physgeo.dpo.dpo_objective_search_v14 \
  --scheme_id E03_smoke10 \
  --steps 10 \
  --gpu 0 \
  --checkpoint_steps 0,5,10 \
  --report_root reports/dpo_utility_calibration_v14/objective_search \
  --output_root local_assets/dpo_utility_calibration_v14/objective_search \
  > reports/dpo_utility_calibration_v14/objective_search/E03_smoke10/stdout.log 2>&1
