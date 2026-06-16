#!/usr/bin/env bash
set -euo pipefail

MANIFEST=""
OUT_ROOT="local_assets/data/physion/generated_v5"
PROFILE="warmup_visible_motion_v5_aggressive_2x_demo"
DISPLAYS=":8"
CHUNK_SIZE="2"
CONFIG="configs/cam_physgeo/tdw_generation_v2.yaml"
VALIDATE_EACH_CHUNK="false"
STOP_RATE="0.10"
NO_OVERWRITE=0
LOG_ROOT=""
REJECT_LLVMPIPE="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest) MANIFEST="$2"; shift 2 ;;
    --out_root) OUT_ROOT="$2"; shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --displays) DISPLAYS="$2"; shift 2 ;;
    --chunk_size) CHUNK_SIZE="$2"; shift 2 ;;
    --config) CONFIG="$2"; shift 2 ;;
    --validate_each_chunk) VALIDATE_EACH_CHUNK="$2"; shift 2 ;;
    --stop_on_chunk_failure_rate) STOP_RATE="$2"; shift 2 ;;
    --log_root) LOG_ROOT="$2"; shift 2 ;;
    --reject_llvpipe) REJECT_LLVMPIPE="$2"; shift 2 ;;
    --no_overwrite) NO_OVERWRITE=1; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$MANIFEST" ]]; then
  echo "--manifest is required" >&2
  exit 2
fi
if [[ ! -f "$MANIFEST" ]]; then
  echo "manifest missing: $MANIFEST" >&2
  exit 2
fi
IFS=, read -r -a DISPLAY_ARR <<< "$DISPLAYS"
if [[ "${#DISPLAY_ARR[@]}" -lt 1 ]]; then
  echo "at least one display is required" >&2
  exit 2
fi

RUN_ID="$(basename "$MANIFEST" .jsonl)_chunks_${CHUNK_SIZE}"
CHUNK_DIR="$(dirname "$MANIFEST")/${RUN_ID}"
if [[ -z "$LOG_ROOT" ]]; then
  LOG_ROOT="$OUT_ROOT/logs/multidisplay_${RUN_ID}"
fi
mkdir -p "$CHUNK_DIR" "$LOG_ROOT" "$OUT_ROOT/reports"

python3 -m cam_physgeo.data.tdw_generation_v2.split_manifest_chunks \
  --manifest "$MANIFEST" \
  --out_dir "$CHUNK_DIR" \
  --chunk_size "$CHUNK_SIZE" \
  --prefix chunk > "$LOG_ROOT/split_summary.json"

mapfile -t CHUNKS < <(find "$CHUNK_DIR" -maxdepth 1 -type f -name chunk_*.jsonl | sort)
if [[ "${#CHUNKS[@]}" -eq 0 ]]; then
  echo "no chunks generated" >&2
  exit 3
fi

echo "manifest=$MANIFEST"
echo "chunks=${#CHUNKS[@]} displays=${DISPLAY_ARR[*]}"
echo "logs=$LOG_ROOT"

if [[ "$REJECT_LLVMPIPE" == "true" ]]; then
  for display in "${DISPLAY_ARR[@]}"; do
    if ! DISPLAY="$display" xdpyinfo >"$LOG_ROOT/xdpyinfo_${display#:}.log" 2>&1; then
      echo "display $display failed xdpyinfo" >&2
      exit 4
    fi
    renderer="$(DISPLAY="$display" glxinfo -B 2>"$LOG_ROOT/glxinfo_${display#:}.err" | grep -E "OpenGL renderer|OpenGL vendor" || true)"
    echo "=== $display renderer ===" >> "$LOG_ROOT/display_renderer.log"
    echo "$renderer" >> "$LOG_ROOT/display_renderer.log"
    if ! echo "$renderer" | grep -q "NVIDIA"; then
      echo "display $display is not NVIDIA OpenGL; refusing TDW generation" >&2
      exit 5
    fi
    if echo "$renderer" | grep -qi "llvmpipe"; then
      echo "display $display is llvmpipe; refusing TDW generation" >&2
      exit 5
    fi
  done
fi

ACTIVE_PIDS=()
ACTIVE_NAMES=()
FAIL=0
TOTAL=0

wait_one_wave() {
  local pid name code
  for idx in "${!ACTIVE_PIDS[@]}"; do
    pid="${ACTIVE_PIDS[$idx]}"
    name="${ACTIVE_NAMES[$idx]}"
    if wait "$pid"; then
      code=0
    else
      code=$?
    fi
    echo "$name exit_code=$code" | tee -a "$LOG_ROOT/wave_status.log"
    TOTAL=$((TOTAL + 1))
    if [[ "$code" -ne 0 ]]; then
      FAIL=$((FAIL + 1))
    fi
  done
  ACTIVE_PIDS=()
  ACTIVE_NAMES=()
  python3 - <<PY
fail=$FAIL
total=max($TOTAL, 1)
rate=fail/total
limit=float("$STOP_RATE")
print(f"chunk_failure_rate={rate:.4f} fail={fail} total={total} limit={limit}")
raise SystemExit(1 if rate > limit else 0)
PY
}

for i in "${!CHUNKS[@]}"; do
  chunk="${CHUNKS[$i]}"
  display="${DISPLAY_ARR[$(( i % ${#DISPLAY_ARR[@]} ))]}"
  name="$(basename "$chunk" .jsonl)__display_${display#:}"
  log="$LOG_ROOT/${name}.log"
  args=(bash scripts/31_run_tdw_generation_v2_smoke.sh --config "$CONFIG" --profile "$PROFILE" --plan "$chunk" --out_root "$OUT_ROOT" --display "$display")
  if [[ "$NO_OVERWRITE" == "1" ]]; then
    args+=(--no_overwrite)
  fi
  echo "launch $name chunk=$chunk display=$display" | tee -a "$LOG_ROOT/launch.log"
  (
    set -euo pipefail
    "${args[@]}"
    if [[ "$VALIDATE_EACH_CHUNK" == "true" ]]; then
      python3 -m cam_physgeo.data.tdw_generation_v2.validate_generated_hdf5 \
        --root "$OUT_ROOT" \
        --manifest "$chunk" \
        --out "$OUT_ROOT/reports/validation_${name}.md" \
        --profile "$PROFILE"
    fi
  ) > "$log" 2>&1 &
  ACTIVE_PIDS+=("$!")
  ACTIVE_NAMES+=("$name")
  if [[ "${#ACTIVE_PIDS[@]}" -ge "${#DISPLAY_ARR[@]}" ]]; then
    wait_one_wave
  fi
done

if [[ "${#ACTIVE_PIDS[@]}" -gt 0 ]]; then
  wait_one_wave
fi

echo "completed total_chunks=$TOTAL failed_chunks=$FAIL logs=$LOG_ROOT"
