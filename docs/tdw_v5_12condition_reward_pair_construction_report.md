# TDW v5 12-Condition Reward Pair Construction Report

Date: 2026-06-12

## Inputs

- Reward scores:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/reward_scoring/12condition/scores.jsonl`
- Rollout root:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/rollout/12condition_base_stageA_stageB`
- Min margin: 0.05
- Min confidence: 0.5
- Max pairs: 100

## Result

- Pair status: no_pairs_ready.
- Pair count: 0.
- Rejected candidate pairs: 60.
- Ready for DPO pilot: false.

## Reason

The reward backend confidence did not meet the pair gate:

- Generated reward confidence average: 0.463235
- Generated real-backend confidence average: 0.411765
- Required minimum confidence: 0.5

The pair builder correctly rejected all candidate pairs rather than emitting low-confidence DPO training data.

## Gate

DPO pilot is not approved from this run. Next step should be reward backend confidence repair or a smaller manual/reward audit before any DPO request.

