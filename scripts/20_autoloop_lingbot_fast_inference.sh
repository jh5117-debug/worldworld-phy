#!/usr/bin/env bash
set -euo pipefail

PY="${LINGBOT_PY:-/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python}"

exec "$PY" -m cam_physgeo.eval.autoloop_fast_inference "$@"
