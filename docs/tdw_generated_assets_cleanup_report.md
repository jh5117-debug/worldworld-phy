# TDW generated assets cleanup report

Cleanup date: 2026-06-06

User instruction: delete previously generated waste data to avoid storage pressure.

Deleted remote generated asset directories:

- `local_assets/data/physion/generated_v2/raw_hdf5/`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_*`
- old partial v3 conversion root: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_50/`

Kept:

- current v3 raw HDF5 review set: `local_assets/data/physion/generated_v3/raw_hdf5/warmup_visible_motion_v3_start0_scene_diverse_plan_50samples/`
- current all-50 v3 LingBot cam-only conversion: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_50_human_accepted_all/`
- generated_v2 manifests/reports for provenance.

Observed storage:

- `generated_v2` before cleanup: about `37G`
- `generated_v2` after cleanup: about `254M`
- available `/home/nvme04` after cleanup and all-50 conversion: about `963G`

No original Physion/TDW data, weights, checkpoints, or current v3 usable data were deleted.
