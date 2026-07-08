#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"
python3 -m cam_physgeo.data.physeditworld_manifest_init \
  --report "${REPORT:-reports/physeditworld_50h/manifest_init/empty_manifest_init.csv}" \
  --json "${JSON:-reports/physeditworld_50h/manifest_init/empty_manifest_init.json}" \
  --summary "${SUMMARY:-reports/physeditworld_50h/manifest_init/empty_manifest_init.md}" \
  ${DRY_RUN:+--dry_run}
