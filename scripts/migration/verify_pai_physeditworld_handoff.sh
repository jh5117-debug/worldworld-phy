#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"
python3 -m cam_physgeo.orchestration.physeditworld_pai_handoff \
  --expected_branch "${EXPECTED_BRANCH:-physion-only-local-assets-videogpa-smoke}" \
  --nas_path "${NAS_PATH:-/mnt/workspace/hj/nas_hj}" \
  --physeditworld_roots "${PHYS_EDITWORLD_ROOTS:-}" \
  --strict_manifest "${STRICT_MANIFEST:-manifests/physeditworld_50h_all.jsonl}" \
  --lingbot_train_manifest "${LINGBOT_TRAIN_MANIFEST:-manifests/physeditworld_50h_lingbot_train.jsonl}" \
  --output_csv "${OUTPUT_CSV:-reports/migration/pai_handoff_status.csv}" \
  --output_json "${OUTPUT_JSON:-reports/migration/pai_handoff_status.json}" \
  --summary "${SUMMARY:-reports/migration/pai_handoff_summary.md}"
