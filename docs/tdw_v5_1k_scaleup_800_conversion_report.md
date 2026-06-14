# TDW v5 1k Scale-Up 800 Conversion Report

Date: 2026-06-14

Output:

`local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_scaleup_800/`

## Result

- Converted samples: 800/800
- target.mp4 files: 800/800
- Conversion errors: 0
- use_action=false
- dummy `action.npy`
- force_rewrite_video=true
- probe_video=true

## Note On Converter Fix

The first conversion attempt returned 0 rows because the converter auto-selected an older demo validation JSON. The converter now supports explicit `--validation_json`; the final successful run used:

`local_assets/data/physion/generated_v3/reports/validation_v5_1k_scaleup_800.json`

