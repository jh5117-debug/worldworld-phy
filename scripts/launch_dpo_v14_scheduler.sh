#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
mkdir -p reports/dpo_utility_calibration_v14
python3 -m cam_physgeo.orchestration.gpu_scheduler_v14 \
  --config configs/cam_physgeo/dpo_v14_scheduler.yaml \
  --state reports/dpo_utility_calibration_v14/scheduler_state.json \
  --heartbeat reports/dpo_utility_calibration_v14/heartbeat.jsonl \
  --report_root reports/dpo_utility_calibration_v14
