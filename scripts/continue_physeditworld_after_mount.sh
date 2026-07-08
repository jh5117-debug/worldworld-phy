#!/usr/bin/env bash
set -euo pipefail
ROOT="${ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$ROOT"

args=(
  --target_hours "${TARGET_HOURS:-50}"
  --limit "${CONVERSION_SMOKE_LIMIT:-32}"
  --root_lock "${ROOT_LOCK:-reports/migration/physeditworld_selected_root.lock.json}"
  --output_csv "${OUTPUT_CSV:-reports/physeditworld_50h/post_mount/post_mount_status.csv}"
  --output_json "${OUTPUT_JSON:-reports/physeditworld_50h/post_mount/post_mount_status.json}"
  --summary "${SUMMARY:-reports/physeditworld_50h/post_mount/post_mount_summary.md}"
)

if [[ -n "${POST_MOUNT_DRY_RUN:-}" ]]; then
  args+=(--dry_run)
fi
if [[ -n "${SKIP_VIDEO_PROBE:-}" ]]; then
  args+=(--skip_video_probe)
fi
if [[ -n "${ALLOW_UNLOCKED_ROOTS:-}" ]]; then
  args+=(--allow_unlocked_roots)
fi
if [[ -n "${RUN_FULL_CONVERSION:-}" ]]; then
  args+=(--run_full_conversion)
fi

python3 -m cam_physgeo.orchestration.physeditworld_post_mount "${args[@]}"
