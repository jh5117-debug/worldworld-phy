#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
export CUDA_VISIBLE_DEVICES=4
python3 -m cam_physgeo.dpo.pair_cache_builder_v8m \
  --pair_manifest reports/dpo_objective_repair_v12b/winner_anchor_diag/s_pass_winner_anchor.jsonl \
  --num_pairs 4 \
  --gpu 0 \
  --prefix_len 5 \
  --prediction_start_frame 5 \
  --future_only true \
  --used_window_frames 49 \
  --output_root local_assets/dpo_objective_repair_v12b/winner_curriculum/cache_s_pass4 \
  --report reports/dpo_objective_repair_v12b/winner_curriculum/cache_s_pass4.csv \
  --progress reports/dpo_objective_repair_v12b/winner_curriculum/cache_s_pass4_progress.jsonl \
  --heartbeat_seconds 15 \
  --per_stage_timeout_seconds 180 \
  --per_pair_timeout_seconds 600 \
  --loader_mode safe_wan_policy_only
python3 -m cam_physgeo.dpo.pair_cache_objective_runner \
  --cache_root local_assets/dpo_objective_repair_v12b/winner_curriculum/cache_s_pass4 \
  --pair_subset local_assets/dpo_objective_repair_v12b/winner_curriculum/cache_s_pass4/cache_index.jsonl \
  --objective winner_anchor_repeat \
  --steps 20 \
  --gpu 0 \
  --output reports/dpo_objective_repair_v12b/winner_curriculum/winner_anchor_s_pass4_20step.csv \
  --scope L0_camera_r4 \
  --used_window_frames 49 \
  --lr 1e-6 \
  --checkpoint_root local_assets/dpo_objective_repair_v12b/winner_curriculum/checkpoints \
  --checkpoint_steps 0,5,10,20 \
  --gradient_checkpointing
