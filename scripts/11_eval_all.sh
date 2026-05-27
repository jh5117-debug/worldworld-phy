#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.eval.camera_audit \
  --config configs/cam_physgeo/stage0_audit.yaml \
  --dry-run \
  --limit "${LIMIT:-2}"
