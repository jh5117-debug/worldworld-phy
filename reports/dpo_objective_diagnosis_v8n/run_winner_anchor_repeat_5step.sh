#!/usr/bin/env bash
set -o pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
export CUDA_VISIBLE_DEVICES=7
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 -m cam_physgeo.dpo.pair_cache_objective_runner \
  --cache_root local_assets/dpo_pair_cache_v8m/gt_c_10_window49 \
  --pair_subset reports/dpo_objective_diagnosis_v8n/pair_selection/delta_ref_positive_pairs.jsonl \
  --objective winner_anchor_repeat \
  --steps 5 \
  --gpu 0 \
  --output reports/dpo_objective_diagnosis_v8n/winner_anchor_repeat_pos8_5step.csv
