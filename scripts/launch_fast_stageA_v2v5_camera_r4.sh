#!/usr/bin/env bash
set -euo pipefail
export FAST_ONLY=1
export FORBID_LINGBOT_BASE=1
export STAGEA_HIGH_ONLY=1
export PC_PREFIX_LEN=5
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src:."
CONFIG="${CONFIG:-configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml}"
DATASET_DIR="${DATASET_DIR:-local_assets/stageA_v2v5_pilot_20260627/dataset}"
OUTPUT_ROOT="${OUTPUT_ROOT:-local_assets/stageA_v2v5_20260627/train}"
EXPERIMENT_NAME="${EXPERIMENT_NAME:-fast_stageA_v2v5_camera_r4_100step}"
NPROC="${NPROC_PER_NODE:-${NPROC:-8}}"
exec scripts/launch_small_lora_scope_sweep.sh "$CONFIG" "$DATASET_DIR" "$OUTPUT_ROOT" "$EXPERIMENT_NAME" "$NPROC" "$@"
