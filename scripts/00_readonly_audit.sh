#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
LOCAL_ASSETS_ROOT="${LOCAL_ASSETS_ROOT:-$PROJECT_ROOT/local_assets}"
cd "$PROJECT_ROOT"
hostname
git status --short
nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv || true
pgrep -af "train_trd_v1|accelerate|run_lingbot_fullval|eval_batch.py|train_stage|cam_physgeo|physion" || echo none
find "$LOCAL_ASSETS_ROOT" -maxdepth 6 -type d \( -iname "*physion*" -o -name synthetic_data_assets \) 2>/dev/null || true
python -m cam_physgeo.data.build_manifest \
  --physion_movingcam_root "$LOCAL_ASSETS_ROOT/data/physion/movingcam_raw" \
  --physion_movingcam_outputs "$LOCAL_ASSETS_ROOT/data/physion/movingcam_outputs" \
  --limit 20 \
  --dry-run
