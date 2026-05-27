#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.training.train_stage3_self_dpo \
  --config configs/cam_physgeo/stage3_self_dpo.yaml \
  --dry-run \
  --limit "${LIMIT:-2}" \
  --max_steps "${MAX_STEPS:-1}"
