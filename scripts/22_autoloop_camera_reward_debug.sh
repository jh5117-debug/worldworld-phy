#!/usr/bin/env bash
set -euo pipefail

export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
export TERM="${TERM:-dumb}"
export TQDM_DISABLE="${TQDM_DISABLE:-1}"
export DISABLE_PROGRESS_BAR="${DISABLE_PROGRESS_BAR:-1}"

python -m cam_physgeo.eval.autoloop_camera_reward_debug "$@"
