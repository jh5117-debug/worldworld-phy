#!/usr/bin/env bash
set -euo pipefail
MANIFEST="${MANIFEST:-manifests/cam_physgeo_all.jsonl}"
python -m cam_physgeo.eval.camera_audit --manifest "$MANIFEST" --out reports/camera_audit.json "${@}"
python -m cam_physgeo.eval.eval_reward_calibration --manifest "$MANIFEST" --out manifests/reward_calibration_scores.jsonl "${@}"
