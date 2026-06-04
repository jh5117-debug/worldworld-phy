# Final Report: TDW Template-Diverse 50-Sample Validation

Date: 2026-06-05

## Approval

The user explicitly approved GPU0-bound `DISPLAY=:8` for exactly one TDW / Physion-style generation v2 `warmup_mild` template-diverse 50-sample validation.

No 200/1k generation was run.

## Generation

Manifest:

`local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_50.jsonl`

Planned and actual distribution:

| Template | Planned | Generated | Validated |
|---|---:|---:|---:|
| `drop` | 15 | 15 | 15 |
| `collision` | 15 | 15 | 15 |
| `roll` | 10 | 10 | 10 |
| `containment` | 10 | 10 | 10 |

Camera variant distribution:

| Camera variant | Count |
|---|---:|
| `orbit_left_12` | 9 |
| `orbit_right_12` | 9 |
| `strafe_left_025` | 8 |
| `strafe_right_025` | 8 |
| `dolly_in_010` | 8 |
| `dolly_out_010` | 8 |

Generation result:

- HDF5 generated: 50/50
- failed commands: 0
- rejected samples: 0
- GPU used: GPU0-bound `DISPLAY=:8`
- approximate generation duration: 1 hour 48 minutes
- raw HDF5 storage: about 4.0 GiB

## Validation

| Check | Result |
|---|---:|
| RGB / `_img` | 50/50 |
| `_depth` | 50/50 |
| `_id` | 50/50 |
| camera pose / position / aim | 50/50 |
| projection / camera matrix | 50/50 |
| object state | 50/50 |
| suitable for warmup | 50/50 |

Visibility:

- `target_visible_ratio`: min 1.0 / avg 1.0 / max 1.0
- max invisible frames: min 0 / avg 0.0 / max 0
- camera path length: min 0.1005 / avg 0.3682 / max 0.8888

## LingBot Conversion

Output:

`local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/`

Result:

- converted samples: 50/50
- target.mp4 probe: 50/50
- target video: 81 frames / 16 fps / 832x480
- `use_action=false`: 50/50
- dummy action zero norm: 50/50
- conversion output storage: about 9.1 GiB

## Video Deliverables

Updated local gallery/index:

- `local_assets/reports/tdw_video_deliverables/video_index.md`
- `local_assets/reports/tdw_video_deliverables/video_gallery.html`

Representative videos:

- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/tdw_v2_00000_drop_orbit_left_12_seed22000_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/tdw_v2_00015_collision_strafe_right_025_seed22015_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/tdw_v2_00030_roll_orbit_left_12_seed22030_0000/target.mp4`
- `local_assets/data/physion/generated_v2/lingbot_cam_inputs_template_diverse_50/tdw_v2_00040_containment_dolly_in_010_seed22040_0000/target.mp4`

## 200 Readiness

200-sample pilot is technically ready but not approved and not run.

Approval request:

`docs/gpu_usage_approval_request_tdw_template_diverse_200.md`

## Safety

- no training
- no DPO training
- no VideoGPA `03_train.py`
- no Stage1
- no LingBot rollout
- no reward calibration
- no LoRA/checkpoint saved
- no 200/1k generation
- no `local_assets` committed

## Next Actions

1. User may approve a 200-sample pilot on GPU0-bound `DISPLAY=:8`.
2. Alternative: configure a GPU6/7 TDW display first.
3. DPO signal remains a separate gate.
4. Full generation only after staged validation and explicit approval.

