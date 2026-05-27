# Physion Camera Metadata Audit

## Moving-Camera Physion/TDW HDF5

Audited sample:

`/home/nvme03/workspace/physion_moving_camera_mainline_20260505/outputs/current_gt_physion_81f_return_fixed_probe12_20260513/collision/00002_collision_relative_yaw_180_reobserve_seed10002/0000.hdf5`

Observed keys include:

- `frames/0000/camera_matrices/camera_matrix`
- `frames/0000/camera_matrices/projection_matrix`
- `frames/0000/labels/camera_pose`
- `frames/0000/labels/camera_position`
- `frames/0000/labels/camera_aim`
- `frames/0000/images/_img`
- `frames/0000/images/_depth`
- `frames/0000/images/_id`
- `frames/0000/objects/positions`
- `frames/0000/objects/velocities`
- `frames/0000/collisions/*`
- `frames/0000/labels/target_contacting_zone`
- `frames/0000/labels/target_on_ground`
- `static/moving_camera/*`

Conclusion: existing Physion/TDW moving-camera HDF5 is directly usable for camera-conditioned LingBot samples. It has explicit extrinsics via `camera_pose`, position/aim fallback, projection/camera matrices, depth, ID, object state, and event labels.

## Official Physion HDF5

Standalone official HDF5 was not confirmed under `/home/nvme03/workspace/physion_official/data`. The new `cam_physgeo.data.physion_hdf5_audit` command must be run after official data is available. If official HDF5 lacks explicit K-style intrinsics, FOV plus resolution or projection matrices can be used to derive intrinsics. If extrinsics are absent, static-camera samples can still support static-camera physics, but they cannot serve as camera-conditioned benchmark samples without regeneration.

## Regeneration Rule

If official samples lack camera metadata, rerun TDW/Physion generation for a subset and export:

- RGB
- depth
- ID mask
- camera_position
- camera_aim
- camera_pose
- projection/intrinsics
- object states
- event metadata
