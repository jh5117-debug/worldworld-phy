# TDW v5 12-Condition dpo_diag Report

Date: 2026-06-12

## Status

- dpo_diag status: `blocked_reward_pair_gate`
- DPO training: not run.
- Winner/loser pairs: not ready.
- Pair count: 0.
- Rejected candidate pairs: 60.

## dpo_diag Files

Remote experiment folder:

`local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/dpo_diag/`

Files written:

- `README.md`
- `dpo_readiness.md`
- `backend_confidence_summary.md`
- `reward_breakdown_summary.md`

## Readiness

- Reward confidence sufficient: no.
- Margin/confidence sufficient for pairs: no.
- Template coverage for pairs: none, because no pairs were emitted.
- `use_action=false` preserved in manifests and scoring wrappers.
- Camera metadata preserved in reward/pair rows where available.

## Recommendation

Do not run DPO yet. Improve reward backend confidence or perform a focused reward audit on the 12-condition rollout outputs.

