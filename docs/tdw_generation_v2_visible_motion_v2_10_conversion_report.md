# TDW Generation v2 Visible-Motion v2 Conversion Report

Input validation report:

`local_assets/data/physion/generated_v2/reports/validation_warmup_visible_motion_v2_10.json`

Output:

`local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_v2_10/`

Conversion result:

- Accepted samples: 10
- Converted samples: 10
- Conversion errors: 0
- `target.mp4` probe: enabled and passed by the converter
- `use_action=false`: enabled
- Dummy `action.npy`: enabled

Required files per sample:

- `image.jpg`
- `target.mp4`
- `poses.npy`
- `intrinsics.npy`
- `prompt.txt`
- `metadata.json`
- `action.npy`

Representative converted samples:

- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_v2_10/tdw_v2_00000_drop_orbit_left_24_seed22000_0000/`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_v2_10/tdw_v2_00003_collision_strafe_left_050_seed22003_0000/`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_v2_10/tdw_v2_00006_roll_strafe_left_050_seed22006_0000/`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_visible_motion_v2_10/tdw_v2_00008_containment_orbit_left_18_seed22008_0000/`

No real action conditioning was used. `action.npy` is a dummy fallback and metadata records `use_action=false`.

