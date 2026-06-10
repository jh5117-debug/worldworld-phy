# TDW v5 4-Condition Reward Scoring Report

Date: 2026-06-10

Input:

`local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/rollout/4condition_base_vs_stageA_adapter/`

Output:

`local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/reward_scoring/4condition_base_vs_adapter/`

Reward version: v5.

Backends requested: RAFT + DINO.

## Summary

Scores completed for GT/Base/Adapter:

- score count: 12;
- GT average confidence-weighted reward: `0.492143`;
- Base average confidence-weighted reward: `0.294709`;
- Adapter average confidence-weighted reward: `0.295647`;
- Adapter > Base count: `2 / 4`;
- Adapter > GT count: `0 / 4`;
- Base > GT count: `0 / 4`.

Backend confidence:

- generated reward confidence avg: `0.463235`;
- generated real-backend confidence avg: `0.411765`;
- trustworthy for pairs: `false`.

The reward direction is sane at the broad GT-vs-generated level: GT scores higher than both Base and Adapter for all four conditions. However, generated-video confidence is below the 0.5 gate, so reward is not trusted for DPO pair construction.

## Per-Condition Scores

| Template | Condition | GT | Base | Adapter | Adapter-Base |
|---|---|---:|---:|---:|---:|
| drop | `tdw_v3_00000_drop_orbit_left_72_seed22000_0000` | 0.486408 | 0.301437 | 0.304226 | 0.002789 |
| collision | `tdw_v3_00093_collision_strafe_left_180_seed22093_0000` | 0.486612 | 0.292593 | 0.294645 | 0.002052 |
| roll | `tdw_v3_00145_roll_orbit_right_60_seed22145_0000` | 0.490484 | 0.289856 | 0.289616 | -0.000241 |
| containment | `tdw_v3_00161_containment_orbit_left_44_seed22161_0000` | 0.505068 | 0.294948 | 0.294103 | -0.000845 |

## Backend Coverage

Clean GT:

- real: `bg`, `cam`, `fg`, `freeze`;
- fallback: `phys`, `quality`;
- missing: `reobs`.

Generated Base and Stage A Adapter:

- real: `bg`, `cam`, `fg`;
- fallback: `freeze`, `phys`, `quality`;
- missing: `reobs`.

This is enough for diagnostic reward inspection, but not enough for winner/loser pair construction under the current confidence gate.

Raw log path:

`local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/logs/4condition_reward_scoring_stdout_stderr.log`

No reward calibration was run and reward weights were not modified.
