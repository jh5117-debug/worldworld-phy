# Download Audit

model_name | purpose | found/downloaded | path | size | load_test | notes
--- | --- | --- | --- | ---: | --- | ---
LingBot-Base | teacher / baseline / branch-style Stage1 warm-up | found | /home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam | 149.246 GB | ok config/layout audit | legacy high_noise_model/low_noise_model + VAE + T5 layout recognized
LingBot-Fast | target fast rollout / DPO policy initialization | found | /home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast | 69.088 GB | ok shard/config audit | 16 safetensors shards; no duplicate download needed
DINOv2-small | foreground identity and reobserve feature similarity | attempted | /home/nvme04/workspace/world_model_phys/PHYS/weight/cam_physgeo_models/dinov2 | partial_or_timeout | download/load audit timed out | reward code falls back to V-JEPA/ID mask/global frame proxy until retry
Depth-Anything-V2-Small | depth fallback for rigid geometry reward | attempted | /home/nvme04/workspace/world_model_phys/PHYS/weight/cam_physgeo_models/depth_anything_v2_small | partial_or_timeout | download/load audit timed out | simulator depth / HDF5 depth and frame proxy remain active
V-JEPA2.1 ViT-B | TRD teacher and temporal physical representation | found | /home/nvme04/workspace/world_model_phys/PHYS/weight/vjepa2_1/vjepa2_1_vitb_dist_vitG_384.pt | 1.6 GB | local checkpoint present | existing local checkpoint used by legacy TRD wrapper
RAFT-small | optical-flow fallback for R_bg/R_cam/P_freeze | found | /home/nvme03/workspace/world_model_phys/external/RAFT/models/raft-small.pth | 102 MB checkout | import/load deferred | existing RAFT checkout; frame-diff proxy remains fallback
SAM2 source | optional foreground/background masks | found | /home/nvme03/workspace/world_model_phys/external/sam2 | source checkout | not loaded | optional; ID masks and simple fallback used first
