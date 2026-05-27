#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.data.physion_regenerate_plan \
  --root /home/nvme03/workspace/physion_moving_camera_mainline_20260505 \
  --limit "${LIMIT:-3}" \
  --dry-run
