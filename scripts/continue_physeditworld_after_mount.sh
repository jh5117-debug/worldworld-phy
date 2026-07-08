#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"
python3 -m cam_physgeo.orchestration.physeditworld_post_mount \
  --output_csv "${OUTPUT_CSV:-reports/physeditworld_50h/post_mount/post_mount_status.csv}" \
  --output_json "${OUTPUT_JSON:-reports/physeditworld_50h/post_mount/post_mount_status.json}" \
  --summary "${SUMMARY:-reports/physeditworld_50h/post_mount/post_mount_summary.md}" \
  ${POST_MOUNT_DRY_RUN:+--dry_run} \
  ${SKIP_VIDEO_PROBE:+--skip_video_probe}
