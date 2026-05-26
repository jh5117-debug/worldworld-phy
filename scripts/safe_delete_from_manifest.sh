#!/usr/bin/env bash
set -euo pipefail
MANIFEST="cleanup/candidate_delete_manifest.tsv"
DRY_RUN=0
ALLOW_HIGH=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --allow-high-risk) ALLOW_HIGH=1 ;;
    --manifest=*) MANIFEST="${arg#--manifest=}" ;;
    --*) echo "Unknown flag: $arg"; exit 2 ;;
    *) MANIFEST="$arg" ;;
  esac
done
if [[ "${CLEANUP_APPROVED:-0}" != "1" ]]; then
  echo "Refusing to delete: set CLEANUP_APPROVED=1 after explicit user approval."
  exit 2
fi
if [[ ! -f "$MANIFEST" ]]; then
  echo "Manifest not found: $MANIFEST"
  exit 2
fi
mkdir -p cleanup
LOG="cleanup/delete_log_$(date +%Y%m%d_%H%M%S).txt"
PROTECTED_RE='(^/home/nvme04/workspace/world_model_phys/PHYS/weight/|PhyInOne|synthetic_data_assets|Lingbot-base|LingBot-Base|Lingbot-Fast|LingBot-Fast|\.safetensors$|\.pth$|\.pt$|\.bin$|\.hdf5$|\.h5$|\.mp4$|/depth($|/)|/id_mask($|/)|/_depth($|/)|/_id($|/))'
echo "manifest=$MANIFEST dry_run=$DRY_RUN allow_high=$ALLOW_HIGH" | tee -a "$LOG"
tail -n +2 "$MANIFEST" | while IFS=$'	' read -r path size_gb type reason risk action; do
  [[ -z "${path:-}" ]] && continue
  if [[ "$path" =~ $PROTECTED_RE ]]; then echo "SKIP protected $path" | tee -a "$LOG"; continue; fi
  if [[ "$risk" == "high" && "$ALLOW_HIGH" != "1" ]]; then echo "SKIP high risk without --allow-high-risk $path" | tee -a "$LOG"; continue; fi
  if [[ ! -e "$path" ]]; then echo "SKIP missing $path" | tee -a "$LOG"; continue; fi
  actual_size=$(du -sh "$path" 2>/dev/null | awk '{print $1}')
  echo "DELETE_CANDIDATE risk=$risk size=$actual_size path=$path reason=$reason" | tee -a "$LOG"
  if [[ "$DRY_RUN" == "1" ]]; then continue; fi
  rm -rf --one-file-system "$path"
  echo "DELETED $path" | tee -a "$LOG"
done
