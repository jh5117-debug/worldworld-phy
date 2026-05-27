#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.data.physion_hdf5_audit \
  --roots /home/nvme03/workspace/physion_official/data /home/nvme03/workspace/physion_moving_camera_mainline_20260505 \
  --out docs/physion_hdf5_key_audit.md \
  --limit "${LIMIT:-30}"
