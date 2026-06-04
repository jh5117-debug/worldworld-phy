# TDW Generation v2 Template-Diverse 50 Conversion Report

Date: 2026-06-05

## Input

Validation JSON:

`local_assets/data/physion/generated_v2/reports/validation_template_diverse_50.json`

Manifest:

`local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_50.jsonl`

## Output

`local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/`

## Result

| Metric | Value |
|---|---:|
| accepted samples | 50 |
| converted samples | 50 |
| conversion errors | 0 |
| target.mp4 probe passed | 50 |
| `image.jpg` exists | 50 |
| `poses.npy` exists | 50 |
| `intrinsics.npy` exists | 50 |
| `action.npy` dummy | 50 |
| action norm zero | 50 |
| `metadata.json use_action=false` | 50 |
| `depth.npy` / `id_mask.npy` | 50 |

Target video properties:

- frames: 81
- fps: 16.0
- size: 832 x 480

Converted template distribution:

| Template | Count |
|---|---:|
| `drop` | 15 |
| `collision` | 15 |
| `roll` | 10 |
| `containment` | 10 |

Camera variant distribution:

| Camera variant | Count |
|---|---:|
| `orbit_left_12` | 9 |
| `orbit_right_12` | 9 |
| `strafe_left_025` | 8 |
| `strafe_right_025` | 8 |
| `dolly_in_010` | 8 |
| `dolly_out_010` | 8 |

## Representative Paths

- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/tdw_v2_00000_drop_orbit_left_12_seed22000_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/tdw_v2_00015_collision_strafe_right_025_seed22015_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/tdw_v2_00030_roll_orbit_left_12_seed22030_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/tdw_v2_00040_containment_dolly_in_010_seed22040_0000/target.mp4`

## Gate

LingBot cam-only conversion for TDW v2 template-diverse 50 validation: passed.

