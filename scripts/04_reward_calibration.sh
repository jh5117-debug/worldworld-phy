#!/usr/bin/env bash
set -euo pipefail
python -m cam_physgeo.eval.eval_reward_calibration --manifest "${MANIFEST:-manifests/cam_physgeo_all.jsonl}" --out "${OUT:-manifests/reward_calibration_scores.jsonl}" "${@}"
