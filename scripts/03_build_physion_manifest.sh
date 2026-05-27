#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.data.build_manifest \
  --physion_official_root "${PHYSION_OFFICIAL_ROOT:-/home/nvme03/workspace/physion_official/data}" \
  --physion_movingcam_root "${PHYSION_MOVINGCAM_ROOT:-/home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets}" \
  --physion_movingcam_outputs "${PHYSION_MOVINGCAM_OUTPUTS:-/home/nvme03/workspace/physion_moving_camera_mainline_20260505/outputs}" \
  --out "${OUT:-manifests/physion_cam_physgeo_smoke.jsonl}" \
  --limit "${LIMIT:-50}"
