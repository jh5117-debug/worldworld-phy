# TDW v3 start0 scene-diverse 50 conversion report

Conversion target:

`local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_50/`

The first pass converted only validator-accepted samples. After human review, the user confirmed that all 50 videos are usable, so the full set was converted into a new all-human-accepted output root.

| Metric | Value |
|---|---:|
| Human-accepted samples | 50 |
| Converted samples | 50 |
| target.mp4 files | 50 |
| Conversion errors | 0 |
| use_action=false | 50 |
| dummy action.npy | 50 |

Required LingBot cam-only files were produced for accepted samples:

- `image.jpg`
- `target.mp4`
- `poses.npy`
- `intrinsics.npy`
- `prompt.txt`
- `metadata.json`
- `action.npy`

The conversion uses dummy fallback action only. Real action is not used, and `metadata.json` records `use_action=false`.

Final conversion root:

`local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_50_human_accepted_all/`

The old partial 28-sample conversion root was removed after the all-50 conversion completed successfully.
