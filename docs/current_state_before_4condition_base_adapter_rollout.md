# Current State Before 4-Condition Base vs Adapter Rollout

Date: 2026-06-10

The active adapter checkpoint was:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

The checkpoint exists on H20 and is adapter-only. It is the tiny Stage A balanced camera-LoRA checkpoint, about 166 KB, containing four LoRA tensors for the camera scale/shift path.

Selected rollout conditions came from the TDW v5 200 test split:

| Template | Sample | Camera |
|---|---|---|
| drop | `tdw_v3_00000_drop_orbit_left_72_seed22000_0000` | `orbit_left_72` |
| collision | `tdw_v3_00093_collision_strafe_left_180_seed22093_0000` | `strafe_left_180` |
| roll | `tdw_v3_00145_roll_orbit_right_60_seed22145_0000` | `orbit_right_60` |
| containment | `tdw_v3_00161_containment_orbit_left_44_seed22161_0000` | `orbit_left_44` |

The approved scope was exactly 4 conditions, base plus Stage A adapter, for at most 8 rollout videos. Reward scoring, pair construction, DPO, VideoGPA `03_train`, Stage1, new TDW generation, and training were not part of this run.

