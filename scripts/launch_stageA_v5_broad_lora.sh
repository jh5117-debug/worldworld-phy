#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
shift || true
if [[ -z "${MODE}" || "${MODE}" == "-h" || "${MODE}" == "--help" ]]; then
  cat <<'EOF'
Usage:
  scripts/launch_stageA_v5_broad_lora.sh --dry-run [args...]
  scripts/launch_stageA_v5_broad_lora.sh --preflight [args...]
  scripts/launch_stageA_v5_broad_lora.sh --run [args...]

Required for preflight/run:
  --dataset_dir PATH
Optional:
  --config PATH
  --branch_mode low|high|sequence
  --output_root PATH
  --nproc_per_node N
  --max_train_optimizer_steps N
  --height N --width N --num_frames N
EOF
  exit 0
fi

CONFIG="configs/cam_physgeo/stageA_v5_broad_lora.yaml"
BRANCH_MODE="low"
DATASET_DIR=""
OUTPUT_ROOT=""
NPROC_PER_NODE="${NPROC_PER_NODE:-1}"
MAX_STEPS=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --branch_mode) BRANCH_MODE="$2"; shift 2 ;;
    --dataset_dir) DATASET_DIR="$2"; shift 2 ;;
    --output_root) OUTPUT_ROOT="$2"; shift 2 ;;
    --nproc_per_node) NPROC_PER_NODE="$2"; shift 2 ;;
    --max_train_optimizer_steps) MAX_STEPS="$2"; shift 2 ;;
    *) EXTRA_ARGS+=("$1"); shift ;;
  esac
done

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-4,5,6,7}"
export CUDA_VISIBLE_DEVICES
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PC_FORCE_LORA_FP32="${PC_FORCE_LORA_FP32:-0}"
export PC_LORA_DISABLE_AUTOCAST="${PC_LORA_DISABLE_AUTOCAST:-0}"
case ",${CUDA_VISIBLE_DEVICES}," in
  *,0,*)
    echo "Refusing to run StageA with GPU0 in CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}" >&2
    exit 3
    ;;
esac

if [[ "${MODE}" == "--dry-run" ]]; then
  echo "mode=dry-run"
  echo "config=${CONFIG}"
  echo "branch_mode=${BRANCH_MODE}"
  echo "dataset_dir=${DATASET_DIR}"
  echo "output_root=${OUTPUT_ROOT}"
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
  echo "nproc_per_node=${NPROC_PER_NODE}"
  echo "max_train_optimizer_steps=${MAX_STEPS:-config_default}"
  exit 0
fi

if [[ -z "${DATASET_DIR}" ]]; then
  echo "--dataset_dir is required for ${MODE}" >&2
  exit 2
fi

RUNNER_ARGS=(--config "${CONFIG}"
  --branch_mode "${BRANCH_MODE}"
  --dataset_dir "${DATASET_DIR}"
  --control_type cam)
if [[ -n "${OUTPUT_ROOT}" ]]; then
  RUNNER_ARGS+=(--output_root "${OUTPUT_ROOT}")
fi
if [[ -n "${MAX_STEPS}" ]]; then
  RUNNER_ARGS+=(--max_train_optimizer_steps "${MAX_STEPS}")
fi
RUNNER_ARGS+=("${EXTRA_ARGS[@]}")

if [[ "${MODE}" == "--preflight" ]]; then
  if [[ -z "${MAX_STEPS}" ]]; then
    RUNNER_ARGS+=(--max_train_optimizer_steps 12)
  fi
  echo "Running single-process StageA preflight on CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
  exec python -m physical_consistency.stages.stage1_physinone_cam.runner "${RUNNER_ARGS[@]}"
fi

if [[ "${MODE}" == "--run" ]]; then
  echo "Running StageA torchrun on CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES} nproc_per_node=${NPROC_PER_NODE}"
  exec torchrun --standalone --nproc_per_node="${NPROC_PER_NODE}" -m physical_consistency.stages.stage1_physinone_cam.runner "${RUNNER_ARGS[@]}"
fi

echo "Unknown mode: ${MODE}" >&2
exit 2
