#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$PROJECT_ROOT"
: "${CUDA_VISIBLE_DEVICES:=6,7}"
export CUDA_VISIBLE_DEVICES
python -m cam_physgeo.eval.run_inference \
  --config configs/cam_physgeo/eval.yaml \
  --model_type fast \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --out local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke \
  --smoke-run \
  --limit "${LIMIT:-10}" \
  --num_frames "${NUM_FRAMES:-16}" \
  --num_steps "${NUM_STEPS:-2}" \
  --resolution "${RESOLUTION:-480x832}" \
  --save_contact_sheet
