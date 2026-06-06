# TDW v3 start0 scene-diverse 50 conversion report

Conversion target:

`local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_50/`

Only accepted samples were converted.

| Metric | Value |
|---|---:|
| Accepted samples | 28 |
| Converted samples | 28 |
| target.mp4 files | 28 |
| Conversion errors | 0 |
| use_action=false | 28 |
| dummy action.npy | 28 |

Required LingBot cam-only files were produced for accepted samples:

- `image.jpg`
- `target.mp4`
- `poses.npy`
- `intrinsics.npy`
- `prompt.txt`
- `metadata.json`
- `action.npy`

The conversion uses dummy fallback action only. Real action is not used, and `metadata.json` records `use_action=false`.

The rejected 22 samples were not converted because `--only_accepted true` filters `too_static` / `delayed_camera_motion` samples.
