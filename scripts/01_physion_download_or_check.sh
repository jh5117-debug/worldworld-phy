#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOCAL_ASSETS_ROOT="${LOCAL_ASSETS_ROOT:-$PROJECT_ROOT/local_assets}"
ROOT="${PHYSION_REPO_ROOT:-$LOCAL_ASSETS_ROOT/third_party/physion_official_repo/physics-benchmarking-neurips2021}"
FALLBACK="$LOCAL_ASSETS_ROOT/third_party/physion_official_repo/physics-benchmarking-neurips2021"
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
