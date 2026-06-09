# TDW v5 200 LingBot Manifest Report

Date: 2026-06-09

## Inputs

- Converted LingBot root: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_200_human_approved_all/`
- Output manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_lingbot_manifest.jsonl`
- Source tag: `tdw_v5_aggressive_2x_200`
- Human approval: `true`

## Result

- Manifest rows: 200
- Missing required files at manifest build: 0
- `use_action=false`: required
- `target.mp4`: required
- camera files: `poses.npy`, `intrinsics.npy` required
- prompt file: required

## Distribution

- Templates: drop 60, collision 60, roll 40, containment 40
- Camera variants:
  - `orbit_left_72`: 60
  - `orbit_right_64`: 30
  - `strafe_left_180`: 30
  - `orbit_right_60`: 40
  - `orbit_left_44`: 40

## Ready For Split

Yes. The manifest has all 200 human-approved LingBot cam-only samples and is ready for integrity audit and train/val/test splitting.
