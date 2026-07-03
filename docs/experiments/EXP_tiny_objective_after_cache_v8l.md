# EXP tiny objective after cache v8l

Current Status: BLOCKED

## Current Status
- v7 tiny SDPO-anchor DPO smoke was an engineering pass but objective-signal fail.
- v8b verified sigma/timestep mapping.
- v8c proved 1-pair/window49 winner-anchor can be memory-safe.
- v8j built and validated a 10-pair winner-side reusable cache.
- v8k completed cache-only 10-pair winner-anchor for 20/20 steps.
- v8l preflight found that the validated v8j cache is intentionally winner-only and has no loser branch.

## Problem
Strict SDPO, Linear-DPO, and safe-linear DPO require both winner and loser policy/reference energies. The current reusable cache contains winner latents, winner mask, and `E_ref_winner_cached`, but no loser latents or `E_ref_loser`. Running SDPO/Linear-DPO on this cache would silently omit the loser term or invent fake loser energy, so it is scientifically invalid.

## Hypothesis
The winner-anchor path is now valid as a component, but pairwise DPO objectives require a reviewed winner+loser pair cache. The correct next step is to build a dual-branch cache from reviewed GT>C pairs before running any tiny SDPO/Linear objective.

## Inputs Checked
- `local_assets/dpo_objective_cache_v8j/gt_c_10_window49/cache_index.jsonl`
- `reports/dpo_objective_diagnosis_v8k/winner_anchor_cache10_20step.csv`
- `cam_physgeo/dpo/objective_ablation.py`

## Preflight Findings
- cache rows: 10
- cache PASS rows: 10
- rows with loser key fields: 0
- rows missing loser energy fields: 10
- rows missing loser tensor/path fields: 10
- v8k mean winner_improvement_post: 1.239776611328125e-05
- v8k final winner_improvement_post: 8.058547973632812e-05

## Success Gate
- Tiny objective may run only after a validated cache contains winner and loser latents, `E_ref_winner`, `E_ref_loser`, same-noise metadata, future masks, and reviewed pair metadata.

## Failure Gate
- If cache is winner-only, do not run SDPO/Linear-DPO.
- If loser visual audit is missing, do not create DPO-ready pair cache.

## Actual Commands Run
- Read v8j cache index and v8k metrics.
- Inspected objective ablation code references for loser energies.
- No DPO, SDPO, Linear-DPO, or safe-linear training was run.

## Actual Outputs
- `reports/dpo_objective_diagnosis_v8l/objective_preflight.md`
- `reports/dpo_objective_diagnosis_v8l/self_review.md`
- `docs/dpo_objective_diagnosis_v8l_status.md`
- `docs/dpo_objective_diagnosis_v8l_report.md`

## Decision
`V8L_BLOCKED_WINNER_ONLY_CACHE_NO_LOSER_ENERGY`

## Next Action
Build `v8m` reviewed pair cache with both winner and loser branches, then validate it before any Strict SDPO / Linear-DPO / safe-linear objective.

## What Is Not Run
- no DPO
- no SDPO
- no Linear-DPO
- no safe-linear
- no large DPO
- no StageB / GRPO / full-data StageA / broad-LoRA
- no pair factory rollout
- no checkpoint deletion
- no video / weight push
