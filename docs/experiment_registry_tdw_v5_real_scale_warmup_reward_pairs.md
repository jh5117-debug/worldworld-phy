# Experiment Registry: TDW v5 Real-Scale Warmup / Rollout / Reward Pairs

Date: 2026-06-11

## Experiment

- Name: `exp_tdw_v5_real_scale_warmup_reward_pairs`
- Folder:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/`
- Dataset: TDW v5 aggressive 2x human-approved 200.
- Status: running Stage A fallback-formal warmup on existing v5 200.

## Paths

- Manifest:
  `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_lingbot_manifest.jsonl`
- Splits:
  `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/`
- Stage A output:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/warmup_stageA/`
- Stage B output:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/warmup_stageB/`
- Rollout output:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/rollout/`
- Reward output:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/reward_scoring/`
- Pair output:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/pair_construction/`
- dpo_diag:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/dpo_diag/`

## dpo_diag

- Current status: `planned_pending_reward_pairs`
- DPO has not run.
- Winner/loser pairs are pending rollout reward scoring.
- Required before DPO: pair source, reward breakdown, margin, confidence, camera metadata, split, and readiness decision.

## Notes

- `local_assets` is a symlink in the helper worktree to the main worktree local assets path.
- This document records paths only; generated videos, checkpoints, and large artifacts are not committed.
