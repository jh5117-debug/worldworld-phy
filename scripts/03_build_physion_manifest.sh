#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOCAL_ASSETS_ROOT="${LOCAL_ASSETS_ROOT:-$PROJECT_ROOT/local_assets}"
"$PY" -m cam_physgeo.data.build_manifest \
  --physion_official_root "${PHYSION_OFFICIAL_ROOT:-$LOCAL_ASSETS_ROOT/data/physion/official}" \
  --physion_movingcam_root "${PHYSION_MOVINGCAM_ROOT:-$LOCAL_ASSETS_ROOT/data/physion/movingcam_raw}" \
  --physion_movingcam_outputs "${PHYSION_MOVINGCAM_OUTPUTS:-$LOCAL_ASSETS_ROOT/data/physion/movingcam_outputs}" \
  --out "${OUT:-$LOCAL_ASSETS_ROOT/data/physion/manifests/physion_cam_physgeo_smoke.jsonl}" \
  --limit "${LIMIT:-50}"
