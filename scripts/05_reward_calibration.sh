#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.eval.eval_reward_calibration \
  --manifest "${MANIFEST:-manifests/physion_cam_physgeo_smoke.jsonl}" \
  --source physion_movingcam \
  --out "${OUT:-reports/reward_calibration_physion_smoke}" \
  --limit "${LIMIT:-10}" \
  --corruptions background_drift object_deformation reobserve_mismatch freeze_foreground global_freeze \
  --save_debug
