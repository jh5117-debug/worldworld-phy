#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOCAL_ASSETS_ROOT="${LOCAL_ASSETS_ROOT:-$PROJECT_ROOT/local_assets}"
"$PY" -m cam_physgeo.data.physion_hdf5_audit \
  --roots "$LOCAL_ASSETS_ROOT/data/physion/movingcam_raw" "$LOCAL_ASSETS_ROOT/data/physion/movingcam_outputs" \
  --out "$LOCAL_ASSETS_ROOT/reports/audits/physion_hdf5_key_audit.md" \
  --limit "${LIMIT:-30}"
