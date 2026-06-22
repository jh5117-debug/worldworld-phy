#!/usr/bin/env bash
set -euo pipefail
if [[ ",${CUDA_VISIBLE_DEVICES:-}," == *",0,"* || "${CUDA_VISIBLE_DEVICES:-}" == "0" || "${CUDA_VISIBLE_DEVICES:-}" == 0,* ]]; then
  echo "Refusing to run Fast StageA on physical GPU0: CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}" >&2
  exit 2
fi
export FAST_ONLY=1
export FORBID_LINGBOT_BASE=1
export STAGEA_HIGH_ONLY=1
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PC_FORCE_LORA_FP32="${PC_FORCE_LORA_FP32:-0}"
export PC_LORA_DISABLE_AUTOCAST="${PC_LORA_DISABLE_AUTOCAST:-0}"
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src:."
PY=${PY:-/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python3.10}
exec "$PY" -m physical_consistency.stages.stage1_physinone_cam.runner \
  --config configs/cam_physgeo/fast_stageA_high_only.yaml \
  --branch_mode high_only \
  "$@"
