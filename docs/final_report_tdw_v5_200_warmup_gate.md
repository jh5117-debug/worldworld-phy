# Final Report: TDW v5 200 LingBot Warmup Gate

Date: 2026-06-09

## Dataset

- Dataset: TDW v5 aggressive 2x 200, manually approved by user as `human_approved_all`.
- LingBot root: `local_assets/data/physion/generated_v3/lingbot_cam_inputs_visible_motion_v5_aggressive_2x_200_human_approved_all/`
- Manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_lingbot_manifest.jsonl`
- Count: 200
- Templates: drop 60, collision 60, roll 40, containment 40
- Camera variants: `orbit_left_72` 60, `orbit_right_64` 30, `strafe_left_180` 30, `orbit_right_60` 40, `orbit_left_44` 40

## Audit

- Valid samples: 200 / 200
- Invalid samples: 0
- Video probe: 200 / 200
- `poses.npy`: `[81, 4, 4]`
- `intrinsics.npy`: `[81, 4, 4]`
- `action.npy`: `[81, 4]`
- `metadata.use_action=false`: passed
- Prompts: non-empty

## Split

- Train: 160
- Val: 20
- Test: 20
- Scene overlap train/val/test: 0
- Balanced by template and camera variant.

## Dataloader

- Passed: yes
- Batch size: 2
- Video shape: `[2, 81, 480, 832, 3]`
- Image shape: `[2, 480, 832, 3]`
- Poses: `[2, 81, 4, 4]`
- Intrinsics: `[2, 81, 4, 4]`
- Action norms: 0.0
- `use_action=false`: passed

## Forward-Loss Dry-Run

- Status: partial / placeholder pass.
- GPU6 was initially busy with a root-owned process. The current user could not kill it because passwordless sudo is unavailable.
- GPU7 was later free and ran the no-backward/no-optimizer/no-checkpoint placeholder tensor path.
- Result: `passed_placeholder_no_model_load`, finite placeholder loss `0.0`.
- Limitation: full LingBot-Fast/VAE/T5 model-load forward-loss smoke has not run yet.

## Experiment Folder

`local_assets/experiments/exp_tdw_v5_200_lingbot_warmup_gate/`

Contains lightweight indexes/reports/log paths only. No generated HDF5/MP4/NPY assets are committed.

`dpo_diag` status: `not_applicable_pre_dpo`. DPO is not part of this experiment and was not run.

## Safety

- No training.
- No DPO.
- No VideoGPA `03_train`.
- No Stage1.
- No rollout.
- No reward calibration.
- No new TDW generation.
- No checkpoint.
- No LoRA saved.
- No `local_assets` committed.

## Next Action

Do not start warmup training yet. Next step is a real LingBot-Fast model-load forward-loss smoke on a free GPU7 or GPU6/7 window, still with no backward, no optimizer, and no checkpoint. After that passes, request explicit approval for a 100 to 200 step warmup pilot.
