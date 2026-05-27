#!/usr/bin/env bash
set -euo pipefail
ROOT="${PHYSION_REPO_ROOT:-/home/nvme03/workspace/physion_official/physics-benchmarking-neurips2021}"
FALLBACK="/home/nvme03/workspace/physion_moving_camera_mainline_20260505/repos/physics-benchmarking-neurips2021"
if [[ -d "$ROOT/.git" ]]; then
  echo "official repo: $ROOT"
elif [[ -d "$FALLBACK/.git" ]]; then
  echo "official repo fallback: $FALLBACK"
else
  mkdir -p "$(dirname "$ROOT")"
  echo "cloning official Physion repo to $ROOT"
  git clone https://github.com/cogtoolslab/physics-benchmarking-neurips2021.git "$ROOT"
fi
git -C "${ROOT:-$FALLBACK}" rev-parse HEAD 2>/dev/null || git -C "$FALLBACK" rev-parse HEAD
echo "Dataset downloads are not launched by this script; inspect README/download size first."
