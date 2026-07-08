#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=${REPO_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}
cd "$REPO_ROOT"
python3 -m cam_physgeo.orchestration.migration_copy_plan \
  --weights_manifest reports/migration/required_weights_manifest.tsv \
  --data_manifest reports/migration/required_data_manifest.tsv \
  --output_tsv reports/migration/approved_copy_manifest_template.tsv \
  --output_json reports/migration/approved_copy_manifest_template.json \
  --summary reports/migration/approved_copy_manifest_template_summary.md
