# TDW Generation v2 LingBot Conversion Probe Report

Generated: 2026-06-04

## Input

- HDF5: `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_1samples/00000_drop_orbit_left_12_seed10000/0000.hdf5`
- Output root: `local_assets/data/physion/generated_v2/lingbot_cam_inputs`
- Sample: `tdw_v2_00000_drop_orbit_left_12_seed10000_0000`
- Conversion command used `--force_rewrite_video true --probe_video true`.
- Python env: `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/.conda_envs/tdw-physion/bin/python`

## Result

`target.mp4` probe passed.

| Item | Value |
|---|---:|
| Converted samples | 1 |
| Conversion errors | 0 |
| target.mp4 exists | yes |
| target.mp4 frames | 81 |
| target.mp4 fps | 16.0 |
| target.mp4 width | 832 |
| target.mp4 height | 480 |
| image.jpg exists | yes |
| poses.npy shape | `(81, 4, 4)` |
| intrinsics.npy shape | `(81, 4, 4)` |
| action.npy shape | `(81, 4)` |
| action norm | 0.0 |
| metadata use_action | false |
| depth.npy exists | yes |
| id_mask.npy exists | yes |

## Warmup Suitability

- Profile: `warmup_mild`
- Template: `drop`
- Camera variant: `orbit_left_12`
- Target visible ratio: `1.0`
- Max invisible frames: `0`
- Camera path length: `0.5927`
- Suitable for LingBot camera-only warmup: yes, as a one-sample smoke candidate.

## Gate Decision

TDW 1-sample LingBot cam-only conversion is now passed. The next TDW 10-sample smoke is still not authorized because it would use GPU0-bound `DISPLAY=:8` unless a GPU6/7 TDW display is configured.
