#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"
python3 -m cam_physgeo.orchestration.physeditworld_locked_handoff \
  --output_csv "${OUTPUT_CSV:-reports/migration/locked_handoff_sequence.csv}" \
  --output_json "${OUTPUT_JSON:-reports/migration/locked_handoff_sequence.json}" \
  --summary "${SUMMARY:-reports/migration/locked_handoff_sequence.md}" \
  ${LOCKED_HANDOFF_DRY_RUN:+--dry_run} \
  ${LOCKED_HANDOFF_CONTINUE_ON_BLOCKED:+--continue_on_blocked}
