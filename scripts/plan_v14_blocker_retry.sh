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
REAL_ENERGY_CMD=(timeout 900s env CUDA_VISIBLE_DEVICES="$GPU" python3 -m cam_physgeo.dpo.utility_calibration_v14 \
  --pair_manifest manifests/dpo_v14_subsets/s_pass.jsonl \
  --subset_name s_pass_retry1 \
  --gpu 0 \
  --policy_init original_or_v12b \
  --reference same_init_frozen \
  --sigma_bins low,mid,high \
  --reduction_modes mean,sum,per_token,local_if_available \
  --limit_pairs 1 \
  --output_csv reports/dpo_utility_calibration_v14/blocker_retry/real_energy_s_pass1.csv \
  --output_jsonl reports/dpo_utility_calibration_v14/blocker_retry/real_energy_s_pass1.jsonl)
LATENT_CMD=(env CUDA_VISIBLE_DEVICES="$GPU" python3 -m cam_physgeo.dpo.latent_relation_monitor_v14 \
  --pair_manifest manifests/dpo_v14_subsets/s_pass.jsonl \
  --subset_name s_pass_retry \
  --output_dir reports/dpo_utility_calibration_v14/blocker_retry/latent_monitor)
printf '%s\n' '# v14 blocker retry commands'
printf 'GPU=%s\n' "$GPU"
printf '\nReal energy retry command:\n'
printf '%q ' "${REAL_ENERGY_CMD[@]}"; printf '\n'
printf '\nLatent monitor retry command:\n'
printf '%q ' "${LATENT_CMD[@]}"; printf '\n'
if [[ "$RUN_V14_BLOCKER_RETRY" != "1" ]]; then
  echo "DRY_RUN_ONLY: set RUN_V14_BLOCKER_RETRY=1 to execute the real-energy smoke."
  exit 0
fi
printf '\nExecuting real-energy retry only. Latent monitor remains manual after backend review.\n'
"${REAL_ENERGY_CMD[@]}"
