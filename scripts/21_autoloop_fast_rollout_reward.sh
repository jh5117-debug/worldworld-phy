#!/usr/bin/env bash
set -euo pipefail

PY="${PY:-/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python}"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python)"
fi

export PYTHONUNBUFFERED=1
export TERM="${TERM:-dumb}"
export TQDM_DISABLE=1
export DISABLE_PROGRESS_BAR=1
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"

exec "$PY" -m cam_physgeo.eval.autoloop_fast_rollout_reward "$@"
