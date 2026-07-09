#!/usr/bin/env bash
set -euo pipefail
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys
PYTHONPATH=. python3 -m cam_physgeo.orchestration.physeditworld_root_onboarding_sequence "$@"
