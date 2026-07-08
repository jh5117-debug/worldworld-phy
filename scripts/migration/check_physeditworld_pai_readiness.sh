#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"
python3 -m cam_physgeo.data.physeditworld_readiness \
  --nas_path "${NAS_PATH:-/mnt/workspace/hj/nas_hj}" \
  --candidate_file "${CANDIDATE_FILE:-reports/migration/physeditworld_candidates_raw.txt}" \
  --strict_manifest "${STRICT_MANIFEST:-manifests/physeditworld_50h_all.jsonl}" \
  --train_manifest "${TRAIN_MANIFEST:-manifests/physeditworld_50h_train.jsonl}" \
  --lingbot_train_manifest "${LINGBOT_TRAIN_MANIFEST:-manifests/physeditworld_50h_lingbot_train.jsonl}" \
  --output_csv "${OUTPUT_CSV:-reports/migration/physeditworld_pai_readiness.csv}" \
  --summary "${SUMMARY:-reports/migration/physeditworld_pai_readiness_summary.md}" \
  --json "${OUTPUT_JSON:-reports/migration/physeditworld_pai_readiness.json}"
