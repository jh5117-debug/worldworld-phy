#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"
python3 -m cam_physgeo.data.physeditworld_root_schema_probe \
  --roots "${PHYS_EDITWORLD_ROOTS:-}" \
  --max_depth "${MAX_DEPTH:-5}" \
  --max_files_per_root "${MAX_FILES_PER_ROOT:-5000}" \
  --output_csv "${OUTPUT_CSV:-reports/migration/physeditworld_root_schema_probe.csv}" \
  --output_json "${OUTPUT_JSON:-reports/migration/physeditworld_root_schema_probe.json}" \
  --summary "${SUMMARY:-reports/migration/physeditworld_root_schema_probe.md}"
