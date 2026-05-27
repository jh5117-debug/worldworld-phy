# Download Audit: Physion

model_name | purpose | found/downloaded | path | size | load_test | notes
--- | --- | --- | --- | ---: | --- | ---
LingBot-Base | teacher / baseline / branch-style warm-up | found | `/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam` | 149.246 GB | layout audit ok | no duplicate download
LingBot-Fast | target policy / fast rollout | found | `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast` | 69.088 GB | shard audit ok | no duplicate download
V-JEPA2.1 ViT-B | TRD teacher | found | `/home/nvme04/workspace/world_model_phys/PHYS/weight/vjepa2_1/vjepa2_1_vitb_dist_vitG_384.pt` | 1.6 GB | local checkpoint present | reused
RAFT-small | optical flow fallback | found | `/home/nvme03/workspace/world_model_phys/external/RAFT/models/raft-small.pth` | about 102 MB | deferred | frame-diff proxy active
DINOv2 | foreground/reobserve features | not blocking | `/home/nvme04/workspace/world_model_phys/PHYS/weight/cam_physgeo_models/dinov2` | partial/unknown | fallback active | retry later if needed
Depth model | generated rollout depth fallback | not blocking | `/home/nvme04/workspace/world_model_phys/PHYS/weight/cam_physgeo_models/depth_anything_v2_small` | partial/unknown | fallback active | Physion GT uses HDF5 depth
SAM/SAM2 | optional masks | optional | `/home/nvme03/workspace/world_model_phys/external/sam2` | source checkout | not loaded | ID mask used first
