# TDW Generation v2 Visible-Motion 10-Sample GPU0 Conversion Report

Date: 2026-06-05

## Summary

Only samples with `suitable_for_visible_motion=true` were converted to LingBot cam-only inputs.

| Item | Value |
|---|---:|
| Validation rows | 10 |
| Visible-motion accepted | 5 |
| Converted | 5 |
| Conversion errors | 0 |
| target.mp4 probe pass | 5 |
| use_action=false | 5 |
| dummy action zero norm | 5 |

## Output Root

```text
local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_10_gpu0
```

## Converted Samples

| Sample | Output dir |
|---|---|
| `tdw_v2_00000_drop_orbit_left_24_seed22000_0000` | `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_10_gpu0/tdw_v2_00000_drop_orbit_left_24_seed22000_0000` |
| `tdw_v2_00001_drop_orbit_right_24_seed22001_0000` | `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_10_gpu0/tdw_v2_00001_drop_orbit_right_24_seed22001_0000` |
| `tdw_v2_00002_drop_orbit_left_28_seed22002_0000` | `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_10_gpu0/tdw_v2_00002_drop_orbit_left_28_seed22002_0000` |
| `tdw_v2_00004_collision_strafe_left_050_seed22004_0000` | `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_10_gpu0/tdw_v2_00004_collision_strafe_left_050_seed22004_0000` |
| `tdw_v2_00005_collision_strafe_right_050_seed22005_0000` | `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_10_gpu0/tdw_v2_00005_collision_strafe_right_050_seed22005_0000` |

Each converted sample contains:

- `image.jpg`
- `target.mp4`
- `poses.npy` with shape `(81, 4, 4)`
- `intrinsics.npy` with shape `(81, 4, 4)`
- `prompt.txt`
- `metadata.json`
- `action.npy` with shape `(81, 4)` and zero norm

`metadata.json` records `use_action=false`.

## Code Note

`convert_generated_to_lingbot.py` now respects `suitable_for_visible_motion` when `--only_accepted true`, so samples rejected as `too_static` or `too_extreme` are not converted into the visible-motion warmup input folder.
