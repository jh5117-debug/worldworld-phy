#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
CUDA_VISIBLE_DEVICES=7 /usr/bin/python3 -m cam_physgeo.dpo.policy_runtime_load_debug \
  --pair_manifest manifests/dpo_smoke_v7_gt_c_10.jsonl \
  --gpu 0 \
  --output reports/dpo_objective_diagnosis_v8h/policy_runtime_load_debug_after_safe_loader.jsonl \
  --heartbeat_seconds 15 \
  --stage_timeout_seconds 300 \
  --loader_mode safe_wan_policy_only \
  --skip_text true \
  --skip_vae true \
  > reports/dpo_objective_diagnosis_v8h/policy_runtime_load_debug_after_safe_loader.stdout.log 2>&1
