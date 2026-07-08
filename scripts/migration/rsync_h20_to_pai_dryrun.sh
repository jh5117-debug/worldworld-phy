#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=${REPO_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}
MIGRATION_ROOT=${MIGRATION_ROOT:-/mnt/workspace/hj/nas_hj/world_model_phys_migration_20260708}
cd "$REPO_ROOT"
mkdir -p "$MIGRATION_ROOT"/{code,env,weights,data,manifests,docs,reports,checksums}
echo "[dry-run] target: $MIGRATION_ROOT"
rsync -avhn --relative   docs/physeditworld_50h_current_status.md   docs/experiments/EXP_physeditworld_50h_prompt_gravity_lingbotfast.md   reports/migration/   scripts/migration/   "$MIGRATION_ROOT/code/"
echo "[dry-run] Weight/data copy is manifest-review-gated."
