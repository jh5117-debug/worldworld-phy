#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOCAL_ASSETS_ROOT="${LOCAL_ASSETS_ROOT:-$PROJECT_ROOT/local_assets}"
"$PY" -m cam_physgeo.data.physion_regenerate_plan \
  --root "$LOCAL_ASSETS_ROOT/data/physion/movingcam_raw" \
  --limit "${LIMIT:-3}" \
  --dry-run
