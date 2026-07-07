#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
export CUDA_VISIBLE_DEVICES=4
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 -m cam_physgeo.eval.run_v2v5_inference \
  --manifest manifests/dpo_v12b_subsets/val_video_4.jsonl \
  --model E06_screen20_step000 \
  --adapter_path local_assets/dpo_utility_calibration_v14/objective_search/E06_screen20/checkpoints/normalized_clipped_loser_L0_camera_r4_step000_lora_state.pt \
  --output_root local_assets/dpo_utility_calibration_v14/objective_search/E06_screen20/rollouts/step000 \
  --max_samples 4 \
  --height 480 --width 832 --num_frames 81 \
  --prefix_len 5 --prediction_start_frame 5 --eval_future_only true \
  --seed 123 --allow_gpu0 --safe_wan_from_pretrained true \
  2>&1 | tee reports/dpo_utility_calibration_v14/objective_search/E06_screen20/checkpoint_eval/step000_rollout.log
