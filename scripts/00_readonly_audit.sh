#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
cd "$PROJECT_ROOT"
hostname
git status --short
nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv || true
pgrep -af "train_trd_v1|train_stage1_phyinone_cam|accelerate|run_lingbot_fullval|eval_batch.py" || echo none
find /home/nvme03/workspace -type d -name synthetic_data_assets 2>/dev/null || true
find /home/nvme04/workspace -type d -name synthetic_data_assets 2>/dev/null || true
python -m cam_physgeo.data.build_manifest --phyinone_root /home/nvme04/workspace/world_model_phys/PHYS/Dataset/Phy_Dataset/PhysInOne_cam --movingcam_root /home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets --limit 20 --dry-run
