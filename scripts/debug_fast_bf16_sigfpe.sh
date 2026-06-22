#!/usr/bin/env bash
set -euo pipefail
if [[ ",${CUDA_VISIBLE_DEVICES:-}," == *",0,"* || "${CUDA_VISIBLE_DEVICES:-}" == "0" || "${CUDA_VISIBLE_DEVICES:-}" == 0,* ]]; then
  echo "Refusing BF16 diagnostic on physical GPU0: CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}" >&2
  exit 2
fi
export PYTHONFAULTHANDLER=1
export TORCH_SHOW_CPP_STACKTRACES=1
export NCCL_DEBUG=${NCCL_DEBUG:-INFO}
export NCCL_ASYNC_ERROR_HANDLING=1
PY=${PY:-/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python}
PYTHONPATH=src:. "$PY" -m cam_physgeo.debug.fast_bf16_sigfpe_repro "$@"
