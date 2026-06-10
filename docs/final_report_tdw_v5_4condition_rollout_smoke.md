# Final Report: TDW v5 4-Condition Base vs Stage A Adapter Rollout Smoke

Date: 2026-06-10

## Setup

Adapter checkpoint:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

Selected conditions:

- drop: `tdw_v3_00000_drop_orbit_left_72_seed22000_0000`, `orbit_left_72`;
- collision: `tdw_v3_00093_collision_strafe_left_180_seed22093_0000`, `strafe_left_180`;
- roll: `tdw_v3_00145_roll_orbit_right_60_seed22145_0000`, `orbit_right_60`;
- containment: `tdw_v3_00161_containment_orbit_left_44_seed22161_0000`, `orbit_left_44`.

GPU: GPU7 via `CUDA_VISIBLE_DEVICES=7`.

No training was run.

## Rollout

Final status: passed.

- Base rollout: 4/4.
- Stage A adapter rollout: 4/4.
- Failed after fix: 0.
- Adapter loaded: yes for all 4 adapter videos.
- Probe: 12/12 videos passed.
- Video format: 81 frames, 16 fps, 832x480.

There was one pre-fix adapter-load failure caused by the runtime script missing the project root on `sys.path`. This was fixed in `run_inference.py`; the adapter-only rerun then passed.

## Human Review

Gallery:

`local_assets/reports/human_review/tdw_v5_stageA_4condition_base_vs_adapter/video_gallery.html`

Videos:

`local_assets/reports/human_review/tdw_v5_stageA_4condition_base_vs_adapter/videos/`

Inspect the GT, Base, and Stage A adapter columns for camera following, background stability, and object consistency.

## Safety

- No DPO.
- No reward scoring.
- No pair construction.
- No VideoGPA `03_train`.
- No Stage1.
- No new TDW generation.
- No checkpoint or LoRA was saved.
- No `local_assets` files are committed.

## Next

Recommended next gate: human review the 4-condition gallery. Then approve one of:

- reward scoring on these 4 conditions;
- a 12-condition base-vs-adapter rollout;
- revise warmup if adapter is visually worse.

DPO remains later.

