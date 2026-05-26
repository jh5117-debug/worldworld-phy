#!/usr/bin/env bash
set -euo pipefail
DRY_RUN=0
for arg in "$@"; do [[ "$arg" == "--dry-run" ]] && DRY_RUN=1; done
CMD=(python -m cam_physgeo.data.build_manifest --phyinone_root /home/nvme04/workspace/world_model_phys/PHYS/Dataset/Phy_Dataset/PhysInOne_cam --movingcam_root /home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets --out manifests/cam_physgeo_all.jsonl)
[[ "$DRY_RUN" == 1 ]] && CMD+=(--dry-run --limit 50)
printf 'Running: %q ' "${CMD[@]}"; echo
"${CMD[@]}"
