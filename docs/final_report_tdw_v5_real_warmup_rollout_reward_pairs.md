# Final Report: TDW v5 Real Warmup / Rollout / Reward Pair Gates

Date: 2026-06-12

## Data

- Used dataset: TDW v5 aggressive 2x human-approved 200.
- 1k TDW scale-up: not run.
- Reason: no GPU4-7 TDW display was available; only GPU0-bound `DISPLAY=:8` was known, and this run did not approve GPU0 TDW generation.
- Active split: train 160 / val 20 / test 20.

## Warmup

Stage A:

- Effective formal run: 206-step high-noise run plus 100-step resume from step-200 adapter.
- Final Stage A adapter:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/warmup_stageA_resume/checkpoint/stageA_high_noise_camera_lora_final/adapter_state.pt`
- No NaN / Inf / OOM.
- No full model checkpoint.
- No optimizer state.

Stage B:

- Mixed high/low/random diagnostic timestep refinement.
- Steps: 200 / 200.
- Final Stage B adapter:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/warmup_stageB/checkpoint/stageB_mixed_camera_lora_final/adapter_state.pt`
- No NaN / Inf / OOM.
- No full model checkpoint.
- No optimizer state.

## Rollout

- Conditions: 12.
- Base videos: 12 / 12.
- Stage A videos: 12 / 12.
- Stage B videos: 12 / 12.
- Total generated rollout videos: 36.
- The adapter rollout initially hit a checkpoint path bug; the wrapper now resolves adapter directories to `adapter_state.pt`.

## Reward

- Scored samples: 48.
- clean_gt avg reward: 0.492272.
- base avg reward: 0.298588.
- Stage A avg reward: 0.296580.
- Stage B avg reward: 0.296515.
- Adapter greater than base count: 3 / 12.
- Generated reward confidence avg: 0.463235.
- Generated real-backend confidence avg: 0.411765.
- `trustworthy_for_pairs`: false.

## Pairs

- Pair count: 0.
- Rejected candidate pairs: 60.
- DPO ready: no.
- Blocker: reward backend confidence below threshold.

## Safety

- DPO training: not run.
- VideoGPA 03_train: not run.
- Stage1: not run.
- Full model finetune: not run.
- Full model checkpoint: not saved.
- local_assets: not committed.

## Next

Recommended next step is not DPO. The next gate should repair or strengthen reward backend confidence, or run a focused manual/reward audit on the 12-condition rollout set. TDW 1k generation remains a separate approval/display issue.

