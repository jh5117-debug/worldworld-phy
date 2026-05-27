#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-python}"
"$PY" -m cam_physgeo.training.train_stage2_anchored_dpo \
  --config configs/cam_physgeo/stage2_anchored_dpo.yaml \
  --pairs "${PAIRS:-manifests/dpo_pairs_physion_gt_vs_corrupt_smoke.jsonl}" \
  --dry-run \
  --limit_pairs "${LIMIT_PAIRS:-2}" \
  --max_steps "${MAX_STEPS:-1}"
