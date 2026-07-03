# DPO Objective Diagnosis v8m Report

Current Status: PASS

## Summary
v8m fixed the v8l blocker by building a reviewed dual-branch winner+loser cache for the same 10 GT>C pairs. The cache includes winner tensors, loser tensors, `E_ref_winner_cached`, `E_ref_loser_cached`, same sigma/timestep metadata, and Codex visual-audit provenance.

## Build / Validation
- 1-pair smoke: PASS
- 1-pair validation: PASS
- 10-pair build: PASS (10 / 10)
- 10-pair validation: PASS (10 / 10)
- output cache root: `local_assets/dpo_pair_cache_v8m/gt_c_10_window49` (not committed)

## Delta_ref Distribution
- positive: 8 / 10
- non-positive: 2 / 10
- mean: 0.10330507159233093
- min: -0.0973658561706543
- max: 0.2931232452392578

## Interpretation
The infrastructure blocker is resolved: the next tiny objective has the required loser branch. Scientifically, the energy backend does not rank every reviewed visual pair in the same direction, so the objective should not scale. The correct next run is a tiny objective diagnosis with pair filtering or pair weights, not large DPO.

## Next Recommended Experiment
`v8n`: cache-only tiny objective diagnosis on the validated v8m pair cache:

- strict SDPO with `lambda_loser=0` until winner improvement is positive;
- Linear-DPO with reward/Delta_ref-aware weights;
- safe-linear only if winner contribution remains positive;
- no large DPO.

## Explicit Non-Runs
No DPO/SDPO/Linear-DPO training, no large DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA, no checkpoint deletion, and no video/weight push occurred in v8m.
