# Final Report: TDW v5 4-Condition Reward Pair Gate

Date: 2026-06-10

## Inputs

Rollout root:

`local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/rollout/4condition_base_vs_stageA_adapter/`

Videos:

- GT: 4/4.
- Base: 4/4.
- Stage A adapter: 4/4.

Conditions: drop, collision, roll, containment.

No new rollout or TDW generation was run.

## Reward

Reward v5 scoring completed with RAFT/DINO requested.

Average confidence-weighted rewards:

- GT: `0.492143`;
- Base: `0.294709`;
- Stage A adapter: `0.295647`.

Per-condition adapter-vs-base:

- drop: `+0.002789`;
- collision: `+0.002052`;
- roll: `-0.000241`;
- containment: `-0.000845`.

Backend confidence:

- generated reward confidence avg: `0.463235`;
- generated real-backend confidence avg: `0.411765`;
- reward trustworthy for pairs: no.

Failure mode:

Generated rows have real `bg/cam/fg`, but `reobs` is missing and `phys/quality/freeze` are fallback-heavy. Adapter-vs-base margins are also very small.

## Pairs

Pair construction was not run.

Accepted pairs: `0`.

Reason: reward confidence gate failed.

## dpo_diag

Path:

`local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/dpo_diag/`

Readiness: not DPO-ready.

## Safety

- No DPO.
- No training.
- No VideoGPA `03_train`.
- No Stage1.
- No new rollout.
- No new TDW generation.
- No reward calibration.
- No local_assets committed.

## Next

Recommended next step: human inspect the 4-condition gallery, then choose one:

- reward backend/debug pass;
- approve 12-condition rollout+reward;
- revise warmup if adapter looks worse.

DPO remains later.
