# TDW Generation v2 10-Sample LingBot Conversion Report

Generated: 2026-06-04

## Command

```bash
python -m cam_physgeo.data.tdw_generation_v2.convert_generated_to_lingbot \
  --root local_assets/data/physion/generated_v2 \
  --out local_assets/data/physion/generated_v2/lingbot_cam_inputs \
  --only_accepted true \
  --num_frames 81 \
  --fps 16 \
  --size 480x832 \
  --use_action false \
  --make_dummy_action true \
  --force_rewrite_video true \
  --probe_video true
```

## Result

The converter read `validation_10sample.json`, which includes 10 new smoke rows plus the previous accepted 1-sample row. The report below filters the 10 new rows under `warmup_mild_10samples`.

| Metric | Value |
|---|---:|
| New 10-sample rows | 10 |
| Converted unique 10-sample dirs | 10 |
| Conversion failures | 0 |
| target.mp4 probe pass count | 10 |
| use_action=false count | 10 |
| dummy action zero count | 10 |
| LingBot cam inputs storage, total tree | 1.9G |

All converted target videos probe as:

- 81 frames
- 16 fps
- 832x480

## Sample Output Paths

- `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00000_drop_orbit_left_12_seed10000_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00001_drop_orbit_right_12_seed10000_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00002_drop_strafe_left_025_seed10000_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00003_drop_strafe_right_025_seed10000_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00004_drop_dolly_in_010_seed10000_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00005_drop_dolly_out_010_seed10000_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00006_drop_orbit_left_12_seed10001_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00007_drop_orbit_right_12_seed10001_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00008_drop_strafe_left_025_seed10001_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00009_drop_strafe_right_025_seed10001_0000/target.mp4`

## Gate Decision

LingBot cam-only conversion passed for the 10-sample smoke. All accepted samples keep `use_action=false`; action is dummy fallback only.
