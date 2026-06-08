# Final report: TDW v5 aggressive 2x 200 generation

## Scope

The user selected the aggressive v5 demo as visually acceptable and asked to clean old surplus data, then generate 200 samples on GPU0 / DISPLAY=:8. This run did not train, did not run DPO, did not run VideoGPA 03_train, did not run Stage1, and did not run 1k generation.

## Cleanup

Old generated surplus assets were removed from previous v3/v4 runs to recover storage. Original Physion data, weights, checkpoints, LingBot weights, and current v5 demo assets were not deleted.

Cleanup report: `docs/tdw_generated_asset_cleanup_before_v5_200_report.md`

## Generation

Profile: `warmup_visible_motion_v5_aggressive_2x_demo`
Generated HDF5: 200/200
Failed generation: 0
Raw HDF5 root: `local_assets/data/physion/generated_v3/raw_hdf5/warmup_visible_motion_v5_aggressive_2x_demo_plan_200samples`

Template distribution: {'drop': 60, 'collision': 60, 'roll': 40, 'containment': 40}
Camera distribution: {'orbit_left_72': 60, 'orbit_right_64': 30, 'strafe_left_180': 30, 'orbit_right_60': 40, 'orbit_left_44': 40}

## Validation

Validation OK: 200/200
Warmup key/visibility gate: 200/200
Strict v5 visible-motion accepted: 44/200
Delayed camera motion: 0/200
Too extreme: 0/200
Unique scene hashes: 200/200

Motion metrics min / avg / max:
- camera_path_length: 1.8034 / 3.2485 / 3.6956
- camera_path_length_first_8_frames: 0.1803 / 0.3249 / 0.3696
- background_motion_proxy: 0.0217 / 0.0390 / 0.0587
- background_motion_proxy_first_8_frames: 0.0179 / 0.0303 / 0.0531
- target_visible_ratio: 1.0000 / 1.0000 / 1.0000

Note: strict v5 accepted count is low because the background-motion proxy threshold is intentionally high. This dataset is marked as `human_approved_all` based on user review of the v5 demo.

## Conversion

Converted target videos: 200/200
`metadata.use_action=false`: 200/200
Dummy `action.npy`: 200/200
Output root: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_200_human_approved_all`

## Review

Review pack: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_200/`
Representative gallery: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_200/video_gallery.html`
Full video symlink folder: `local_assets/reports/human_review/tdw_visible_motion_v5_aggressive_2x_200/videos/`

## Safety

No training. No DPO. No VideoGPA 03_train. No Stage1. No LingBot rollout. No reward calibration. No 1k generation. Generated HDF5/MP4/NPY assets remain under `local_assets` and must not be committed.
