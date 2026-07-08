#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=${REPO_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}
cd "$REPO_ROOT"
python3 -m cam_physgeo.orchestration.migration_approved_copy \
  --copy_plan reports/migration/approved_copy_manifest_template.tsv \
  --migration_root "${MIGRATION_ROOT:-/mnt/workspace/hj/nas_hj/world_model_phys_migration_20260708}" \
  --output_csv reports/migration/approved_copy_status.csv \
  --output_json reports/migration/approved_copy_status.json \
  --summary reports/migration/approved_copy_status_summary.md \
  "$@"
