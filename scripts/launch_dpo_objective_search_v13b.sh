#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work
mkdir -p reports/dpo_objective_search_v13b
python3 -m cam_physgeo.orchestration.gpu_scheduler_v13b --config configs/cam_physgeo/dpo_objective_search_v13b.yaml --state reports/dpo_objective_search_v13b/scheduler_state.json --heartbeat reports/dpo_objective_search_v13b/heartbeat.jsonl --report_root reports/dpo_objective_search_v13b
