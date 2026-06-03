#!/usr/bin/env bash
set -euo pipefail
CONFIG="configs/cam_physgeo/tdw_generation_v2.yaml"
PROFILE="warmup_mild"
NUM_TRIALS="1"
OUT_ROOT="local_assets/data/physion/generated_v2"
DRY_RUN=0
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --num_trials) NUM_TRIALS="$2"; shift 2 ;;
    --out_root) OUT_ROOT="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --no_overwrite) EXTRA+=("--no_overwrite"); shift ;;
    *) EXTRA+=("$1"); shift ;;
  esac
done
CMD=(python3 -m cam_physgeo.data.tdw_generation_v2.run_tdw_trial --config "$CONFIG" --profile "$PROFILE" --num_trials "$NUM_TRIALS" --out_root "$OUT_ROOT" "${EXTRA[@]}")
if [[ "$DRY_RUN" == "1" ]]; then CMD+=(--dry-run); else CMD+=(--execute_existing_batch); fi
"${CMD[@]}"
