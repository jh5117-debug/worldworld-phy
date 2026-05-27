#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
LOCAL_ASSETS_ROOT="${LOCAL_ASSETS_ROOT:-$PROJECT_ROOT/local_assets}"
ONLY="all"
DRY_RUN=1
SKIP_EXISTING=0
CHECKSUM=0
OVERWRITE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --only) ONLY="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --run) DRY_RUN=0; shift ;;
    --skip-existing) SKIP_EXISTING=1; shift ;;
    --checksum) CHECKSUM=1; shift ;;
    --overwrite) OVERWRITE=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

SRC_MOVINGCAM_RAW="${SRC_MOVINGCAM_RAW:-/home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets}"
SRC_MOVINGCAM_OUTPUTS="${SRC_MOVINGCAM_OUTPUTS:-/home/nvme03/workspace/physion_moving_camera_mainline_20260505/outputs}"
SRC_LINGBOT_FAST="${SRC_LINGBOT_FAST:-/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast}"
SRC_LINGBOT_BASE="${SRC_LINGBOT_BASE:-/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam}"
SRC_VJEPA2="${SRC_VJEPA2:-/home/nvme04/workspace/world_model_phys/PHYS/weight/vjepa2_1}"
SRC_RAFT="${SRC_RAFT:-/home/nvme03/workspace/world_model_phys/external/RAFT}"
SRC_LINGBOT_CODE="${SRC_LINGBOT_CODE:-/home/nvme03/workspace/lingbot-world}"

mkdir -p "$LOCAL_ASSETS_ROOT"/reports/audits
LOG="$LOCAL_ASSETS_ROOT/reports/audits/asset_migration_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1

echo "migration_log=$LOG"
echo "only=$ONLY dry_run=$DRY_RUN skip_existing=$SKIP_EXISTING checksum=$CHECKSUM overwrite=$OVERWRITE"

rsync_one() {
  local kind="$1" src="$2" dst="$3"
  [[ -e "$src" ]] || { echo "SKIP missing $src"; return 0; }
  mkdir -p "$dst"
  if [[ "$OVERWRITE" != 1 && -n "$(find "$dst" -mindepth 1 -maxdepth 1 2>/dev/null | head -1)" ]]; then
    echo "target_nonempty=$dst"
    if [[ "$SKIP_EXISTING" != 1 ]]; then
      echo "Refusing to copy into nonempty target without --skip-existing or --overwrite"
      return 2
    fi
  fi
  local args=(-aH --info=progress2 --partial)
  [[ "$DRY_RUN" == 1 ]] && args+=(--dry-run)
  [[ "$SKIP_EXISTING" == 1 ]] && args+=(--ignore-existing)
  [[ "$CHECKSUM" == 1 ]] && args+=(--checksum)
  [[ "$OVERWRITE" != 1 ]] && args+=(--update)
  echo
  echo "RSYNC[$kind]: $src/ -> $dst/"
  rsync "${args[@]}" "$src"/ "$dst"/
  echo "VERIFY[$kind]"
  echo -n "source_files="; find "$src" -type f 2>/dev/null | wc -l
  echo -n "target_files="; find "$dst" -type f 2>/dev/null | wc -l
  du -sh "$src" "$dst" 2>/dev/null || true
}

rsync_lingbot_code() {
  local src="$SRC_LINGBOT_CODE" dst="$LOCAL_ASSETS_ROOT/third_party/lingbot_world"
  [[ -e "$src" ]] || { echo "SKIP missing $src"; return 0; }
  mkdir -p "$dst"
  local args=(-aH --info=progress2 --partial --exclude='.conda_envs/' --exclude='lingbot-world-base-cam/' --exclude='**/wandb/' --exclude='**/outputs/' --exclude='**/checkpoints/' --exclude='**/*.safetensors' --exclude='**/*.pth' --exclude='**/*.pt' --exclude='**/*.bin')
  [[ "$DRY_RUN" == 1 ]] && args+=(--dry-run)
  [[ "$SKIP_EXISTING" == 1 ]] && args+=(--ignore-existing)
  [[ "$CHECKSUM" == 1 ]] && args+=(--checksum)
  [[ "$OVERWRITE" != 1 ]] && args+=(--update)
  echo
  echo "RSYNC[lingbot_code_filtered]: $src/ -> $dst/"
  rsync "${args[@]}" "$src"/ "$dst"/
  echo -n "target_files="; find "$dst" -type f 2>/dev/null | wc -l
  du -sh "$dst" 2>/dev/null || true
}

case "$ONLY" in
  data|all)
    rsync_one data_raw "$SRC_MOVINGCAM_RAW" "$LOCAL_ASSETS_ROOT/data/physion/movingcam_raw"
    rsync_one data_outputs "$SRC_MOVINGCAM_OUTPUTS" "$LOCAL_ASSETS_ROOT/data/physion/movingcam_outputs"
    ;;&
  weights|all)
    rsync_one lingbot_fast "$SRC_LINGBOT_FAST" "$LOCAL_ASSETS_ROOT/weights/lingbot_fast"
    rsync_one lingbot_base "$SRC_LINGBOT_BASE" "$LOCAL_ASSETS_ROOT/weights/lingbot_base"
    rsync_one vjepa2 "$SRC_VJEPA2" "$LOCAL_ASSETS_ROOT/weights/vjepa2"
    rsync_one raft "$SRC_RAFT" "$LOCAL_ASSETS_ROOT/weights/optical_flow/RAFT"
    ;;&
  third_party|all)
    rsync_lingbot_code
    ;;&
esac

echo "done"
