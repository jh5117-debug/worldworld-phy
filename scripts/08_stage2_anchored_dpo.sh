#!/usr/bin/env bash
set -euo pipefail
python -m cam_physgeo.training.train_stage2_anchored_dpo --config configs/cam_physgeo/stage2_anchored_dpo.yaml --dry-run "${@}"
