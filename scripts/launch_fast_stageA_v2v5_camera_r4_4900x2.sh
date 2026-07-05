#!/usr/bin/env bash
set -euo pipefail
export FAST_ONLY=1
export FORBID_LINGBOT_BASE=1
export STAGEA_HIGH_ONLY=1
export PC_PREFIX_LEN=5
export PYTHONNOUSERSITE=1
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src:."
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-4,5,6,7}"
CONFIG="${CONFIG:-configs/cam_physgeo/fast_stageA_v2v5_camera_r4_4900x2.yaml}"
DATASET_DIR="${DATASET_DIR:-local_assets/stageA_v2v5_4900x2/dataset}"
OUTPUT_ROOT="${OUTPUT_ROOT:-local_assets/stageA_v2v5_4900x2/train}"
EXPERIMENT_NAME="${EXPERIMENT_NAME:-fast_stageA_v2v5_camera_r4_4900x2}"
NPROC="${NPROC_PER_NODE:-${NPROC:-4}}"
train_csv="$DATASET_DIR/metadata_train.csv"
test_csv="$DATASET_DIR/metadata_test.csv"
if [[ ! -f "$train_csv" || ! -f "$test_csv" ]]; then
  echo "BLOCKED: missing 4900/100 metadata split at $DATASET_DIR" >&2
  exit 42
fi
train_rows=$(( $(wc -l < "$train_csv") - 1 ))
test_rows=$(( $(wc -l < "$test_csv") - 1 ))
if [[ "$train_rows" -ne 4900 || "$test_rows" -ne 100 ]]; then
  echo "BLOCKED: expected train=4900 test=100, got train=$train_rows test=$test_rows" >&2
  exit 43
fi
case ",$CUDA_VISIBLE_DEVICES," in
  *",0,"*|*",1,"*|*",2,"*|*",3,"*)
    echo "BLOCKED: CUDA_VISIBLE_DEVICES must not include physical GPU0-3: $CUDA_VISIBLE_DEVICES" >&2
    exit 44
    ;;
esac
exec scripts/launch_small_lora_scope_sweep.sh "$CONFIG" "$DATASET_DIR" "$OUTPUT_ROOT" "$EXPERIMENT_NAME" "$NPROC" "$@"
