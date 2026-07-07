#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
export CUDA_VISIBLE_DEVICES=4
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 -m cam_physgeo.dpo.dpo_objective_search_v14 \
  --scheme_id E01_screen20 \
  --steps 20 \
  --gpu 0 \
  --checkpoint_steps 0,10,20 \
  --report_root reports/dpo_utility_calibration_v14/objective_search \
  --output_root local_assets/dpo_utility_calibration_v14/objective_search \
  2>&1 | tee reports/dpo_utility_calibration_v14/objective_search/E01_screen20/run.log
