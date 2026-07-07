#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
mkdir -p reports/dpo_utility_calibration_v14/blocker_retry
: "${RUN_V14_BLOCKER_RETRY:=0}"
GPU="${V14_RETRY_GPU:-4}"
if [[ "$GPU" != "4" && "$GPU" != "5" ]]; then
  echo "REFUSE_FORBIDDEN_GPU: V14_RETRY_GPU must be 4 or 5, got $GPU" >&2
  exit 2
fi
REAL_ENERGY_CMD=(timeout 900s env CUDA_VISIBLE_DEVICES="$GPU" python3 -m cam_physgeo.dpo.full_real_energy_audit run-shard \
  --pair_manifest manifests/dpo_v14_subsets/s_pass.jsonl \
  --config configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml \
  --out_dir reports/dpo_utility_calibration_v14/blocker_retry/real_energy_s_pass1_full_audit \
  --repo_root . \
  --device cuda \
  --runtime_device cpu \
  --condition_manifest manifests/screen16_v2v5.jsonl \
  --prefix_len 5 \
  --num_frames 81 \
  --height 480 \
  --width 832 \
  --seed_base 91400 \
  --shard_index 0 \
  --num_shards 1 \
  --limit 1 \
  --resume)
LATENT_CMD=(python3 -m cam_physgeo.dpo.latent_relation_monitor_v14 \
  --search_roots /home/nvme03 /home/nvme04 \
  --output_dir reports/dpo_utility_calibration_v14/blocker_retry/latent_monitor \
  --max_dirs 5000 \
  --max_seconds 20)
printf '%s\n' '# v14 blocker retry commands'
printf 'GPU=%s\n' "$GPU"
printf '\nReal energy retry command:\n'
printf '%q ' "${REAL_ENERGY_CMD[@]}"; printf '\n'
printf '\nLatent monitor backend audit command:\n'
printf '%q ' "${LATENT_CMD[@]}"; printf '\n'
if [[ "$RUN_V14_BLOCKER_RETRY" != "1" ]]; then
  echo "DRY_RUN_ONLY: set RUN_V14_BLOCKER_RETRY=1 to execute the real-energy smoke."
  exit 0
fi
printf '\nExecuting real-energy retry only. Latent monitor remains manual after backend review.\n'
"${REAL_ENERGY_CMD[@]}"
