#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.dpo.pair_builder \
  --manifest "${MANIFEST:-manifests/physion_cam_physgeo_smoke.jsonl}" \
  --source physion_movingcam \
  --pair_types gt_vs_corrupt \
  --out "${OUT:-manifests/dpo_pairs_physion_gt_vs_corrupt_smoke.jsonl}" \
  --corruptions background_drift object_deformation reobserve_mismatch freeze_foreground global_freeze \
  --limit "${LIMIT:-10}" \
  --min_margin "${MIN_MARGIN:-0.15}" \
  --save_videos "${SAVE_VIDEOS:-outputs/dpo_pair_physion_smoke}" \
  --save_report "${SAVE_REPORT:-reports/dpo_pair_builder_physion_smoke.md}"
