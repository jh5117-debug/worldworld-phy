#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 5 ]]; then
  echo "usage: $0 <config> <dataset_dir> <output_root> <experiment_name> <nproc_per_node> [runner args...]" >&2
  exit 2
fi
CONFIG=$1
DATASET_DIR=$2
OUTPUT_ROOT=$3
EXPERIMENT_NAME=$4
NPROC=$5
shift 5
export FAST_ONLY=1
export FORBID_LINGBOT_BASE=1
export STAGEA_HIGH_ONLY=1
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PC_FORCE_LORA_FP32="${PC_FORCE_LORA_FP32:-0}"
export PC_LORA_DISABLE_AUTOCAST="${PC_LORA_DISABLE_AUTOCAST:-0}"
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src:."
PY=${PY:-/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python3.10}
if [[ "$NPROC" == "1" ]]; then
  exec "$PY" -m physical_consistency.stages.stage1_physinone_cam.runner     --config "$CONFIG"     --branch_mode high_only     --dataset_dir "$DATASET_DIR"     --output_root "$OUTPUT_ROOT"     --experiment_name "$EXPERIMENT_NAME"     "$@"
fi
exec torchrun --standalone --nproc_per_node="$NPROC"   -m physical_consistency.stages.stage1_physinone_cam.runner   --config "$CONFIG"   --branch_mode high_only   --dataset_dir "$DATASET_DIR"   --output_root "$OUTPUT_ROOT"   --experiment_name "$EXPERIMENT_NAME"   "$@"
