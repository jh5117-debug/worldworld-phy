# DPO Objective Diagnosis v8m Status

Current Status: PASS

Generated: 2026-07-03T02:38:45.438241+00:00

## Result
Reviewed winner+loser pair cache construction completed and validated.

- one-pair smoke: PASS
- one-pair validation: PASS
- 10-pair build: PASS (10 / 10)
- 10-pair validation: PASS (10 / 10)
- cache root: `local_assets/dpo_pair_cache_v8m/gt_c_10_window49` (not committed)
- build report: `reports/dpo_objective_diagnosis_v8m/pair_cache_build_10pair.csv`
- validation report: `reports/dpo_objective_diagnosis_v8m/pair_cache_validation_10pair.csv`

## Reference Energy Readback
- Delta_ref positive: 8 / 10
- Delta_ref non-positive: 2 / 10
- Delta_ref mean: 0.10330507159233093
- Delta_ref min: -0.0973658561706543
- Delta_ref max: 0.2931232452392578

## Decision
`PAIR_CACHE10_VALIDATED_FOR_TINY_OBJECTIVE`

## Caveat
Do not blindly use all 10 pairs as equally strong preferences. Two rows have non-positive `Delta_ref` under the current energy backend, so the next tiny objective should either filter them or use reward/Delta_ref-aware pair weighting.

## Explicit Non-Runs
No DPO, SDPO, Linear-DPO, safe-linear, large DPO, StageB, GRPO, full-data StageA, broad-LoRA, pair rollout, checkpoint deletion, or video/weight push was run in v8m.
