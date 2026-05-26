# Data Locations

## PhyInOne

Found PhyInOne roots under:

- `/home/nvme04/workspace/world_model_phys/PHYS/Dataset/Phy_Dataset/PhysInOne/raw`
- `/home/nvme04/workspace/world_model_phys/PHYS/Dataset/Phy_Dataset/PhysInOne_cam`
- `/home/nvme04/workspace/world_model_phys/PHYS/Dataset/Phy_Dataset/PhysInOne_cam_smoke`
- `/home/nvme04/workspace/world_model_phys/PHYS/Dataset/Phy_Dataset/PhysInOne_cam_75f_384`

`PhysInOne_cam` contains 2472 `video.mp4` clips with matching `poses.npy` and `intrinsics.npy` in the sampled audit.

## moving-camera synthetic extension data

Found `synthetic_data_assets` roots:

- Primary `MOVING_CAM_ROOT`: `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets`
- Secondary generated functional files root: `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/generation_functional_files_20260525/synthetic_data_assets`

The primary root points to local asset symlinks and the authoritative output root:

- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/outputs`

Audit counts from the output root:

- HDF5/H5 files: 330
- MP4 previews/videos: 281
- Templates visible in paths: `drop`, `collision`, `roll`, `containment`; `support` is expected mainly from PhyInOne.
- Camera motions visible in paths: `lookaway_up_reobserve`, `occluder_lookaway_reobserve`, `offscreen_x_reobserve`, `offscreen_z_reobserve`, `relative_yaw_180_reobserve`.
- Metadata sidecars visible: `tdw_commands.json`, `summary.json`, `batch_config.json`.
- HDF5 implies simulator RGB/depth/ID/camera metadata, but key names require Stage 0 HDF5 key audit before relying on them.
