# Final Report: TDW v5 Scale-Up / Warmup / Reward Pair Gates

Date: 2026-06-10

## Data

No new TDW data was generated.

Current selected dataset is TDW v5 aggressive 2x 200 human-approved:

- manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_lingbot_manifest.jsonl`;
- split: train/val/test = 160/20/20;
- total template distribution: drop 60, collision 60, roll 40, containment 40.

Scale-up did not run because TDW still needs a confirmed display. Prior audits only confirmed GPU0-bound `DISPLAY=:8`; this task did not approve GPU0 for TDW generation.

## Warmup

No new warmup was run.

The active adapter remains the previous balanced Stage A checkpoint:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

The 300-step warmup was not run because the prior 60-step run took about 9028 seconds, so 300 steps likely exceeds the 12-hour approval threshold.

## Rollout

Real rollout was not run.

This branch adds the missing adapter inference path:

- `run_inference.py` now loads the Stage A runtime LoRA adapter;
- `rollout_compare_base_adapter.py` can run base-vs-adapter comparisons from the v5 manifest.

Because 12 conditions means 24 LingBot-Fast generations at 81 frames, this should be approved as a long-running GPU job before launch.

A remote dry-run did pass for a 4-condition rollout plan:

- drop: `tdw_v3_00000_drop_orbit_left_72_seed22000_0000`;
- collision: `tdw_v3_00093_collision_strafe_left_180_seed22093_0000`;
- roll: `tdw_v3_00145_roll_orbit_right_60_seed22145_0000`;
- containment: `tdw_v3_00161_containment_orbit_left_44_seed22161_0000`.

No videos were generated.

## Reward

Reward scoring was not run because rollout videos were not produced.

Added:

- `score_rollouts.py`, which scores GT/base/adapter rows and records backend confidence.

## Pair Construction

No winner/loser pairs were built.

Added:

- `build_reward_pairs.py`, which only emits pairs when reward margin and confidence thresholds pass.

## dpo_diag

Status: `planned_pending_pairs`.

DPO is not ready.

## Safety

- No DPO.
- No VideoGPA `03_train`.
- No Stage1.
- No new TDW data.
- No new warmup training.
- No rollout.
- No reward calibration.
- No full checkpoint.
- No `local_assets` committed.

## Next

Recommended next action: approve a 4-condition base-vs-Stage-A-adapter rollout smoke first. If runtime and videos look acceptable, expand to 12 conditions, then run reward scoring and pair construction.
