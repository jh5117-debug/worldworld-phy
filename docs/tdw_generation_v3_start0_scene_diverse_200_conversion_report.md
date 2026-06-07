# TDW v3 start0 scene-diverse 200 conversion report

Conversion root:

`local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v3_start0_scene_diverse_200_human_accepted_all/`

Conversion result:

| Metric | Value |
|---|---:|
| Human-accepted samples | 200 |
| Converted samples | 200 |
| target.mp4 files | 200 |
| Conversion errors | 0 |
| use_action=false | 200 |
| dummy action.npy | 200 |

Required LingBot cam-only files:

- `image.jpg`
- `target.mp4`
- `poses.npy`
- `intrinsics.npy`
- `prompt.txt`
- `metadata.json`
- `action.npy`

The conversion uses dummy fallback action only. Real action is not used, and `metadata.json` records `use_action=false`.

Storage:

- converted all-200 LingBot cam-only root: about `37G`
