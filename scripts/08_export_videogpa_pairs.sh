#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
PAIRS="${PAIRS:-local_assets/data/physion/processed/dpo_pairs/smoke/dpo_pairs_physion_gt_vs_corrupt.jsonl}"
OUT="${OUT:-local_assets/data/physion/processed/dpo_pairs/smoke/videogpa_pairs.json}"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --pairs) PAIRS="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

args=(-m cam_physgeo.dpo.export_videogpa_pairs --pairs "${PAIRS}" --out "${OUT}" --format videogpa)
if [[ "${DRY_RUN}" == "1" ]]; then
  args+=(--dry-run)
fi

"${PYTHON_BIN}" "${args[@]}"
