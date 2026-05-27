#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys}"
LOCAL_ASSETS_ROOT="${LOCAL_ASSETS_ROOT:-$PROJECT_ROOT/local_assets}"

SRC_MOVINGCAM_RAW="${SRC_MOVINGCAM_RAW:-/home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets}"
SRC_MOVINGCAM_OUTPUTS="${SRC_MOVINGCAM_OUTPUTS:-/home/nvme03/workspace/physion_moving_camera_mainline_20260505/outputs}"
SRC_LINGBOT_FAST="${SRC_LINGBOT_FAST:-/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast}"
SRC_LINGBOT_BASE="${SRC_LINGBOT_BASE:-/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam}"
SRC_VJEPA2="${SRC_VJEPA2:-/home/nvme04/workspace/world_model_phys/PHYS/weight/vjepa2_1}"
SRC_RAFT="${SRC_RAFT:-/home/nvme03/workspace/world_model_phys/external/RAFT}"

mkdir -p "$LOCAL_ASSETS_ROOT"/{data/physion/{movingcam_raw,movingcam_outputs,official,processed/{lingbot_cam_inputs,corruptions,dpo_pairs,rollouts},manifests,splits},weights/{lingbot_fast,lingbot_base,dinov2,vjepa2,videomae2,optical_flow,depth,other},third_party/{VideoGPA,geometryflow_optional,physion_official_repo,lingbot_world},reports/{audits,reward_calibration,dpo_pair_builder,smoke,contact_sheets,figures},outputs/{smoke,eval,inference,temporary},cache/{hf,torch,video_features},logs}

echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "LOCAL_ASSETS_ROOT=$LOCAL_ASSETS_ROOT"
echo
echo "Source -> target plan:"
printf '%s\t%s\n' "$SRC_MOVINGCAM_RAW" "$LOCAL_ASSETS_ROOT/data/physion/movingcam_raw"
printf '%s\t%s\n' "$SRC_MOVINGCAM_OUTPUTS" "$LOCAL_ASSETS_ROOT/data/physion/movingcam_outputs"
printf '%s\t%s\n' "$SRC_LINGBOT_FAST" "$LOCAL_ASSETS_ROOT/weights/lingbot_fast"
printf '%s\t%s\n' "$SRC_LINGBOT_BASE" "$LOCAL_ASSETS_ROOT/weights/lingbot_base"
printf '%s\t%s\n' "$SRC_VJEPA2" "$LOCAL_ASSETS_ROOT/weights/vjepa2"
printf '%s\t%s\n' "$SRC_RAFT" "$LOCAL_ASSETS_ROOT/weights/optical_flow/RAFT"
echo
echo "Sizes:"
for p in "$SRC_MOVINGCAM_RAW" "$SRC_MOVINGCAM_OUTPUTS" "$SRC_LINGBOT_FAST" "$SRC_LINGBOT_BASE" "$SRC_VJEPA2" "$SRC_RAFT"; do
  printf '%s\t' "$p"
  du -sh "$p" 2>/dev/null || echo "missing"
done
echo
df -h "$PROJECT_ROOT" "$LOCAL_ASSETS_ROOT" 2>/dev/null || df -h "$PROJECT_ROOT"
echo
echo "Dry-run only: this script does not copy files."
