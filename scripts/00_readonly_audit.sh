#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$PROJECT_ROOT"
hostname
git status --short
nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv || true
pgrep -af "train_trd_v1|accelerate|run_lingbot_fullval|eval_batch.py|train_stage|cam_physgeo|physion" || echo none
find /home/nvme03/workspace /home/nvme04/workspace -maxdepth 5 -type d \( -iname "*physion*" -o -name synthetic_data_assets \) 2>/dev/null || true
python -m cam_physgeo.data.build_manifest \
  --physion_movingcam_root /home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets \
  --physion_movingcam_outputs /home/nvme03/workspace/physion_moving_camera_mainline_20260505/outputs \
  --limit 20 \
  --dry-run
