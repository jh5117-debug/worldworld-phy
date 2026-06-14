# TDW v5 1000 LingBot Manifest / Audit Report

Date: 2026-06-14

Manifest:

`local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest.jsonl`

Audit:

`local_assets/experiments/exp_tdw_v5_aggressive_2x_1k_generation/validation/audit_1000.json`

## Manifest

- Rows: 1000
- Existing 200 root: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_200_human_approved_all/`
- New 800 root: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_scaleup_800/`
- human_approved=true
- source_tag=`tdw_v5_aggressive_2x_1000`
- error_count=0

Template distribution:

- drop: 300
- collision: 300
- roll: 200
- containment: 200

Camera distribution:

- orbit_left_72: 300
- orbit_right_60: 200
- orbit_left_44: 200
- orbit_right_64: 150
- strafe_left_180: 150

## Audit

- Total samples: 1000
- Valid samples: 1000
- Invalid samples: 0
- target.mp4 probe pass: 1000
- Duplicate sample IDs: 0
- ready_for_dataloader: true

Numpy shape summary:

- poses.npy: `[81, 4, 4]` for 1000 samples
- intrinsics.npy: `[81, 4, 4]` for 1000 samples
- action.npy: `[81, 4]` for 1000 samples

The audit uses imageio fallback video probing when ffprobe/cv2 are unavailable in the runtime environment.

