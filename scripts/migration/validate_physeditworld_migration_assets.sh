#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=${REPO_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}
cd "$REPO_ROOT"
python3 -m cam_physgeo.orchestration.migration_asset_validator \
  --weights_manifest reports/migration/required_weights_manifest.tsv \
  --data_manifest reports/migration/required_data_manifest.tsv \
  --nas_root /mnt/workspace/hj/nas_hj \
  --execute_script scripts/migration/rsync_h20_to_pai_execute.sh \
  --output_csv reports/migration/migration_asset_validation.csv \
  --output_json reports/migration/migration_asset_validation.json \
  --summary reports/migration/migration_asset_validation_summary.md
