#!/usr/bin/env bash
set -euo pipefail
python -m cam_physgeo.eval.run_inference --manifest "${MANIFEST:-manifests/cam_physgeo_val.jsonl}" --out "${OUT:-outputs/cam_physgeo_rollouts}" --dry-run "${@}"
