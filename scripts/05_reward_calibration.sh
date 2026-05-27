#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.eval.eval_reward_calibration \
  --manifest "${MANIFEST:-local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl}" \
  --source physion_movingcam \
  --out "${OUT:-local_assets/reports/reward_calibration/smoke_20}" \
  --limit "${LIMIT:-10}" \
  --corruptions background_drift object_deformation object_color_identity_change reobserve_mismatch freeze_foreground global_freeze \
  --strength "${STRENGTH:-medium}" \
  --device "${DEVICE:-cpu}" \
  --gpu_ids "${GPU_IDS:-}" \
  --save_debug
