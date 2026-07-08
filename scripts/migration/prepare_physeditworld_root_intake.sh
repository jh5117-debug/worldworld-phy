#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"
python3 -m cam_physgeo.orchestration.physeditworld_root_intake \
  --physeditworld_roots "${PHYS_EDITWORLD_ROOTS:-}" \
  --output_json "${OUTPUT_JSON:-reports/migration/physeditworld_root_intake.json}" \
  --summary "${SUMMARY:-reports/migration/physeditworld_root_intake.md}"
