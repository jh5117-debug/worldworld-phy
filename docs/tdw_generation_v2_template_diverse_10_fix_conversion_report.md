# TDW Generation v2 Template-Diverse 10 Conversion Report

Date: 2026-06-04

## Input

Validation report:

`local_assets/data/physion/generated_v2/reports/validation_template_diverse_10_fix.json`

Output:

`local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_fix/`

## Code Fix Included

The converter now maps manifest suffixes to matching validation files. For this run:

`plan_warmup_mild_template_diverse_10_fix.jsonl`

maps to:

`validation_template_diverse_10_fix.json`

The video probe utility also now has an `imageio` fallback, because the TDW env has `imageio_ffmpeg` but lacks `cv2` and system `ffprobe`.

## Result

| Metric | Value |
|---|---:|
| accepted samples | 10 |
| converted samples | 10 |
| conversion errors | 0 |
| target.mp4 probe pass | 10 |
| frames / fps / size | 81 / 16.0 / 832x480 |
| `use_action=false` | 10 |
| dummy `action.npy` zero norm | 10 |

Each sample contains:

- `image.jpg`
- `target.mp4`
- `poses.npy`
- `intrinsics.npy`
- `prompt.txt`
- `metadata.json`
- `action.npy`
- `depth.npy`
- `id_mask.npy`

## Sample Outputs

- `tdw_v2_00000_drop_orbit_left_12_seed22000_0000`
- `tdw_v2_00003_collision_strafe_right_025_seed22003_0000`
- `tdw_v2_00006_roll_orbit_left_12_seed22006_0000`
- `tdw_v2_00008_containment_strafe_left_025_seed22008_0000`

## Gate

LingBot cam-only conversion for template-diverse TDW v2 smoke: passed.

