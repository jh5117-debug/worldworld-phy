#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.training.train_stage1_physion_warmup \
  --config configs/cam_physgeo/stage1_physion_warmup.yaml \
  --dry-run \
  --limit "${LIMIT:-2}" \
  --max_steps "${MAX_STEPS:-1}"
