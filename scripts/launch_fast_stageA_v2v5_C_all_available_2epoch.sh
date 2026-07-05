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
CONFIG="${CONFIG:-configs/cam_physgeo/fast_stageA_v2v5_C_camera_self_last4_r4_all_available_2epoch.yaml}"
DATASET_DIR="${DATASET_DIR:-local_assets/stageA_v2v5_all_available_c_r4_2epoch/dataset}"
OUTPUT_ROOT="${OUTPUT_ROOT:-local_assets/stageA_v2v5_all_available_c_r4_2epoch/train}"
EXPERIMENT_NAME="${EXPERIMENT_NAME:-fast_stageA_v2v5_C_camera_self_last4_r4_all_available_2epoch}"
NPROC="${NPROC_PER_NODE:-${NPROC:-4}}"
train_csv="$DATASET_DIR/metadata_train.csv"
val_csv="$DATASET_DIR/metadata_val.csv"
if [[ ! -f "$train_csv" || ! -f "$val_csv" ]]; then
  echo "BLOCKED: missing all-available metadata split at $DATASET_DIR" >&2
  exit 42
fi
train_rows=$(( $(wc -l < "$train_csv") - 1 ))
val_rows=$(( $(wc -l < "$val_csv") - 1 ))
if [[ "$train_rows" -lt 1 || "$val_rows" -lt 1 ]]; then
  echo "BLOCKED: empty train/val metadata: train=$train_rows val=$val_rows" >&2
  exit 43
fi
case ",$CUDA_VISIBLE_DEVICES," in
  *",0,"*|*",1,"*|*",2,"*|*",3,"*)
    echo "BLOCKED: CUDA_VISIBLE_DEVICES must not include physical GPU0-3: $CUDA_VISIBLE_DEVICES" >&2
    exit 44
    ;;
esac
echo "Launching all-available C-scope warmup: train_rows=$train_rows val_rows=$val_rows CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES nproc=$NPROC"
exec scripts/launch_small_lora_scope_sweep.sh "$CONFIG" "$DATASET_DIR" "$OUTPUT_ROOT" "$EXPERIMENT_NAME" "$NPROC" "$@"
