#!/usr/bin/env bash
set -euo pipefail
python -m cam_physgeo.training.train_stage3_self_dpo --config configs/cam_physgeo/stage3_self_dpo.yaml --dry-run "${@}"
