# DPO Objective Ablation Report

Updated: 2026-06-28 21:02:04

## Current Decision

S0_sanity_8 / S_localdpo_16 was executed with the real LingBot-Fast prefix-aware V2V-5 energy backend. All four tiny probes were runtime-stable, but the training-signal gate failed. Therefore S1_probe_20 was not launched, and this branch should not scale DPO yet.

This is not a CUDA or BF16 failure. It is an objective/pair-signal failure: the losses remain near the no-signal 0.693 region, winner improvement is weak or negative, and the margin is mostly from loser degradation.

## Subsets

- S0_sanity_8: 8 pairs, 4 Type B strongest energy-margin rollout losers + 4 Type A strongest local corruptions.
- S1_probe_20: 20 pairs prepared but not run because S0 failed.
- S2_probe_32_optional: prepared only, not run.
- S_localdpo_16: 16 Type A local-corruption pairs used for LocalDPO-style diagnostic objective.

## Objective Summary

| objective | runtime | steps | dpo_loss first -> last | implicit acc first -> last | winner improvement mean/last | loser degradation mean/last | winner contribution mean/last | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| standard | PASS | 20.0 | 0.693147 -> 0.693153 | 0.000 -> 0.000 | 5.70324e-05 / -0.000293121 | -0.00020108 / 0.000186637 | 0.330 / 0.000 | FAILED_WEAK_SIGNAL |
| sdpo | PASS | 20.0 | 0.693147 -> 0.693109 | 0.000 -> 1.000 | -4.42055e-05 / 0.000229828 | 9.42908e-05 / 0.000533 | 0.211 / 0.301 | FAILED_LOSER_ONLY_OR_WINNER_WORSE |
| linear | PASS | 20.0 | 0.693147 -> 0.693147 | 0.000 -> 1.000 | 3.98584e-05 / -6.50324e-05 | 0.000113499 / 6.77127e-05 | 0.263 / 0.000 | FAILED_LOSER_ONLY_OR_WINNER_WORSE |
| localdpo | PASS | 20.0 | 0.693147 -> 0.693058 | 0.000 -> 1.000 | -0.000177636 / -0.000671133 | 0.000441797 / 0.00245741 | 0.262 / 0.000 | FAILED_LOSER_ONLY_OR_WINNER_WORSE |

## Interpretation

- Standard energy-DPO is runtime-stable but has weak signal: final DPO loss remains about 0.693 and final winner improvement is negative.
- SDPO-style winner-preserving objective is the least bad S0 result: final winner improvement is positive and final winner contribution is just over 0.30, but mean winner improvement is still negative and the mean winner contribution is below gate. This is not enough to run S1.
- Linear-DPO-style diagnostic objective increases gradient magnitude but still ends with winner worsening and loser-only margin risk.
- LocalDPO-style affected-time objective is runtime-stable but is clearly loser-dominant on this implementation/subset; spatial region masks are still TODO.

## Video Evaluation Status

Checkpoint videos were not expanded after S0 because the training-signal gate failed. The instruction for this run was to stop training and report if S0 fails. Running a large checkpoint video sweep after a failed objective gate would consume time without changing the core decision. Existing checkpoints are preserved under local_assets for later optional visual inspection.

## Artifacts

- S0 root: `local_assets/dpo_objective_ablation_20260628_184115/`
- Training signal summary: `reports/dpo_objective_ablation/s0_training_signal_summary.csv`
- Subset summary: `reports/dpo_objective_ablation/subset_summary.csv`
- Subset manifests: `manifests/dpo_probe_subsets/`

## Decision

Status: DPO_OBJECTIVE_ABLATION_S0_FAILED_SIGNAL. Do not scale Standard, Linear, or LocalDPO-style objective. SDPO-style is the only objective worth revisiting, but it needs a stronger winner-preserving formulation and probably better pair weighting before S1.

## Next Step

Before any DPO training scale-up, improve the objective so winner_improvement is consistently positive and winner_contribution_ratio is above 0.30 on average. Recommended next small test: SDPO-style with an explicit winner-preservation term and loser lambda capped below 0.25 until winner energy improves.
