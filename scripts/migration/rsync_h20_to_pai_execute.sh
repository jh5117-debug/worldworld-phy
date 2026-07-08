#!/usr/bin/env bash
set -euo pipefail
if [[ "${MIGRATION_APPROVED:-0}" != "1" ]]; then
  echo "Refusing to execute migration without MIGRATION_APPROVED=1" >&2
  exit 2
fi
REPO_ROOT=${REPO_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}
MIGRATION_ROOT=${MIGRATION_ROOT:-/mnt/workspace/hj/nas_hj/world_model_phys_migration_20260708}
cd "$REPO_ROOT"
mkdir -p "$MIGRATION_ROOT"/{code,env,weights,data,manifests,docs,reports,checksums}
rsync -avh --relative   docs/physeditworld_50h_current_status.md   docs/experiments/EXP_physeditworld_50h_prompt_gravity_lingbotfast.md   reports/migration/   scripts/migration/   "$MIGRATION_ROOT/code/"
echo "Manifest-driven weight/data copy is intentionally not automatic yet."
echo "Review required_*_manifest.tsv, remove unneeded candidates, and add explicit approved copy list first."
