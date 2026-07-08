#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"
python3 -m cam_physgeo.orchestration.physeditworld_completion_audit \
  --output_csv "${OUTPUT_CSV:-reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.csv}" \
  --output_json "${OUTPUT_JSON:-reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json}" \
  --summary "${SUMMARY:-reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.md}"
