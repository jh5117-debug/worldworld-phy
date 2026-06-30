#!/usr/bin/env bash
set -u
OUT=${1:-reports/targeted_BC_loser_mining_v6/gpu_status_before.csv}
mkdir -p "$(dirname "$OUT")"
run_section() {
  local name="$1"; shift
  echo "# ${name}"
  local tmp
  tmp=$(mktemp)
  setsid "$@" > "$tmp" 2>&1 &
  local pid=$!
  local done_flag=0
  for _ in $(seq 1 10); do
    if ! kill -0 "$pid" 2>/dev/null; then
      done_flag=1
      break
    fi
    sleep 1
  done
  if [ "$done_flag" = "1" ]; then
    cat "$tmp"
    wait "$pid" 2>/dev/null || true
  else
    echo "${name}_TIMEOUT_AFTER_10S"
    kill -TERM -"$pid" 2>/dev/null || true
    sleep 1
    kill -KILL -"$pid" 2>/dev/null || true
  fi
  rm -f "$tmp"
}
{
  echo "# safe_gpu_status $(date -Ins) host=$(hostname)"
  run_section query_gpu nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv
  run_section pmon nvidia-smi pmon -c 1
  run_section compute_apps nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv
  echo "# fallback"
  echo "fallback_full_nvidia_smi_skipped_to_avoid_hang"
} > "$OUT"
echo "$OUT"
