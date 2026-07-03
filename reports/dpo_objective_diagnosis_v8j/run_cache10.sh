#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
CUDA_VISIBLE_DEVICES=7 python3 -m cam_physgeo.dpo.winner_anchor_cache_builder \
  --pair_manifest manifests/dpo_smoke_v7_gt_c_10.jsonl \
  --num_pairs 10 \
  --gpu 0 \
  --prefix_len 5 \
  --prediction_start_frame 5 \
  --future_only true \
  --used_window_frames 49 \
  --cache_level with_ref_energy \
  --loader_mode safe_wan_policy_only \
  --output_root local_assets/dpo_objective_cache_v8j/gt_c_10_window49 \
  --report reports/dpo_objective_diagnosis_v8j/cache_build_10pair_with_ref.csv \
  --progress reports/dpo_objective_diagnosis_v8j/cache_build_10pair_progress.jsonl \
  --heartbeat_seconds 15 \
  --per_pair_timeout_seconds 600 \
  --per_stage_timeout_seconds 180 \
  > reports/dpo_objective_diagnosis_v8j/cache_build_10pair.stdout.log 2>&1
