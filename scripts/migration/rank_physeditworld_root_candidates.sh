#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"
python3 -m cam_physgeo.data.physeditworld_root_candidates \
  --candidate_file "${CANDIDATE_FILE:-reports/migration/physeditworld_candidates_raw.txt}" \
  --explicit_roots "${PHYS_EDITWORLD_ROOTS:-}" \
  --max_depth "${MAX_DEPTH:-3}" \
  --max_files_per_root "${MAX_FILES_PER_ROOT:-500}" \
  --top_k "${TOP_K:-25}" \
  --output_csv "${OUTPUT_CSV:-reports/migration/physeditworld_root_candidates_ranked.csv}" \
  --output_json "${OUTPUT_JSON:-reports/migration/physeditworld_root_candidates_ranked.json}" \
  --summary "${SUMMARY:-reports/migration/physeditworld_root_candidates_ranked.md}"
