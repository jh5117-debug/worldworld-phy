#!/usr/bin/env bash
set -euo pipefail
BRANCH="${BRANCH:-physion-only-local-assets-videogpa-smoke}"
REPO_URL="${REPO_URL:-git@github-worldworld-phy-deploy:jh5117-debug/worldworld-phy.git}"
PAI_ROOT="${PAI_ROOT:-/mnt/workspace/hj/nas_hj/world_model_phys_migration_20260708/code}"
REPO_DIR="${REPO_DIR:-$PAI_ROOT/world_model_phys}"
mkdir -p "$PAI_ROOT"
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
else
  cd "$REPO_DIR"
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git merge --ff-only "origin/$BRANCH"
fi
cd "$REPO_DIR"
printf 'repo=%s\nbranch=%s\nhead=%s\n' "$REPO_DIR" "$(git branch --show-current)" "$(git rev-parse --short HEAD)"
python3 -V || true
bash scripts/migration/init_physeditworld_empty_manifests.sh || true
bash scripts/migration/verify_pai_physeditworld_handoff.sh || true
bash scripts/migration/run_physeditworld_phase0_preflight.sh || true
bash scripts/run_physeditworld_pipeline_gates.sh || true
python3 -m cam_physgeo.orchestration.physeditworld_requirement_matrix || true
printf 'Bootstrap complete. Inspect reports/migration, reports/physeditworld_50h/pipeline_gate, and reports/physeditworld_50h/requirement_matrix.*\n'
