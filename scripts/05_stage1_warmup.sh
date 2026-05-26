#!/usr/bin/env bash
set -euo pipefail
python -m cam_physgeo.training.train_stage1_warmup --config configs/cam_physgeo/stage1_warmup.yaml --dry-run "${@}"
