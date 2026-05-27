#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.dpo.pair_builder \
  --manifest "${MANIFEST:-local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl}" \
  --source physion_movingcam \
  --pair_types gt_vs_corrupt \
  --out "${OUT:-local_assets/data/physion/processed/dpo_pairs/smoke/dpo_pairs_physion_gt_vs_corrupt.jsonl}" \
  --corruptions background_drift object_deformation object_color_identity_change reobserve_mismatch freeze_foreground global_freeze \
  --limit "${LIMIT:-10}" \
  --min_margin "${MIN_MARGIN:-0.15}" \
  --save_videos "${SAVE_VIDEOS:-local_assets/data/physion/processed/dpo_pairs/smoke/videos}" \
  --save_report "${SAVE_REPORT:-local_assets/reports/dpo_pair_builder/smoke_report.md}"
