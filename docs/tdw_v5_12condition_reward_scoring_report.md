# TDW v5 12-Condition Reward Scoring Report

Date: 2026-06-12

## Inputs

- Rollout root:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/rollout/12condition_base_stageA_stageB`
- Scored labels:
  - clean_gt: 12
  - base: 12
  - stageA_adapter: 12
  - stageB_adapter: 12
- Total scored samples: 48.
- Reward version: v5.
- RAFT / DINO: enabled.
- Reward calibration: not run.

## Aggregate Scores

Confidence-weighted reward averages:

- clean_gt: 0.492272
- base: 0.298588
- Stage A adapter: 0.296580
- Stage B adapter: 0.296515

Adapter-vs-base:

- Comparable conditions: 12
- Adapter greater than base count: 3

## Backend Confidence

- Generated reward confidence average: 0.463235
- Generated real-backend confidence average: 0.411765
- `trustworthy_for_pairs`: false

Backend coverage:

- Real components for generated videos: bg / cam / fg.
- Fallback components for generated videos: freeze / phys / quality.
- Missing component: reobs.

## Gate

Reward scoring completed, but the reward gate does not pass for DPO pair construction because generated confidence and real-backend confidence are both below 0.5.

DPO remains blocked.

