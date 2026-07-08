#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=${REPO_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}
cd "$REPO_ROOT"
python3 -m cam_physgeo.orchestration.physeditworld_phase0_preflight "$@"
