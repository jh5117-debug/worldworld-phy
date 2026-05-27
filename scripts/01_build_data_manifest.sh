#!/usr/bin/env bash
set -euo pipefail
DRY_RUN=0
for arg in "$@"; do [[ "$arg" == "--dry-run" ]] && DRY_RUN=1; done
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOCAL_ASSETS_ROOT="${LOCAL_ASSETS_ROOT:-$PROJECT_ROOT/local_assets}"
CMD=(python -m cam_physgeo.data.build_manifest
  --physion_official_root "$LOCAL_ASSETS_ROOT/data/physion/official"
  --physion_movingcam_root "$LOCAL_ASSETS_ROOT/data/physion/movingcam_raw"
  --physion_movingcam_outputs "$LOCAL_ASSETS_ROOT/data/physion/movingcam_outputs"
  --out "$LOCAL_ASSETS_ROOT/data/physion/manifests/physion_cam_physgeo_all.jsonl")
[[ "$DRY_RUN" == 1 ]] && CMD+=(--dry-run --limit 50)
printf 'Running: %q ' "${CMD[@]}"; echo
"${CMD[@]}"
