#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"
python3 -m cam_physgeo.orchestration.physeditworld_pipeline_gate \
  --run_readiness \
  --output_csv "${OUTPUT_CSV:-reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.csv}" \
  --output_json "${OUTPUT_JSON:-reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json}" \
  --summary "${SUMMARY:-reports/physeditworld_50h/pipeline_gate/pipeline_gate_summary.md}"
