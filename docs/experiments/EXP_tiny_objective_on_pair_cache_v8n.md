# EXP tiny objective on pair cache v8n

Current Status: PLANNED

Generated: 2026-07-03T05:47:13.247626+00:00

## Current Status
- v8k cache10 winner-anchor PASS.
- v8l correctly blocked objective execution on a winner-only cache.
- v8m reviewed winner+loser cache is valid: 10 / 10 build PASS and 10 / 10 validation PASS.
- Delta_ref positive pairs: 8 / 10.
- Delta_ref non-positive pairs: 2 / 10.

## Problem
v7 SDPO-anchor was loser-dominant and did not preserve the winner. v8k proved a winner-anchor loop can improve winner energy, but it did not include a loser branch. v8m now provides a real winner+loser cache; v8n must diagnose whether tiny preference objectives can produce winner-preserving signal without scaling.

## Hypothesis
Strict SDPO with `lambda_loser=0` until winner improvement is stable can protect the winner. Linear-DPO-style utility may avoid sigmoid no-margin stagnation. Safe-linear may combine both. The Delta_ref-positive subset should be more reliable than mixing in the two non-positive rows at full weight.

## Inputs
- cache root: `local_assets/dpo_pair_cache_v8m/gt_c_10_window49`
- cache validation: `reports/dpo_objective_diagnosis_v8m/pair_cache_validation_10pair.csv`
- build report: `reports/dpo_objective_diagnosis_v8m/pair_cache_build_10pair.csv`

## GPU
- H20 GPU4-7 only.
- Prefer physical GPU7 via `CUDA_VISIBLE_DEVICES=7` and process `--gpu 0`.
- No physical GPU0-3.

## Objectives
A. `forward_sanity` on Delta_ref-positive subset.
B. `winner_anchor_repeat` on Delta_ref-positive subset.
C. `strict_sdpo` on Delta_ref-positive subset.
D. `linear_dpo_anchor` on Delta_ref-positive subset.
E. `safe_linear` on Delta_ref-positive subset.
F. `standard_dpo_baseline` max 5 steps as diagnostic only.
G. no-train diagnostic for Delta_ref non-positive pairs.

## Pair Selection Rule
- `S_pos8`: all `Delta_ref > 0` rows, expected count 8.
- `S_top5`: top 5 positive rows by `Delta_ref`.
- `S_bad2`: rows with `Delta_ref <= 0`, diagnostic only.
- `S_all10_weighted`: not the default objective subset; non-positive rows weight 0 or diagnostic weight only.

## Metrics
- winner_improvement_post
- loser_degradation_post
- winner_contribution_ratio_post
- reference_relative_margin_post
- grad_norm
- update_norm
- objective_loss
- OOM / NaN / SIGFPE status

## Success Gate
- no OOM / SIGFPE / NaN;
- objective loop enters optimizer;
- grad nonzero;
- update_norm > 0;
- mean and final winner_improvement_post > 0;
- winner_contribution_ratio >= 0.30;
- loser degradation is not the only margin source;
- objective does not remain pure 0.693 no-signal.

## Failure Gate
- cache schema invalid;
- hidden loser branch missing;
- OOM / NaN / SIGFPE;
- grad zero or update_norm zero;
- winner_improvement <= 0;
- winner_contribution_ratio < 0.30;
- Delta_ref-positive subset not learnable.

## Output Paths
- `reports/dpo_objective_diagnosis_v8n/`
- `docs/dpo_objective_diagnosis_v8n_report.md`
- `reports/dpo_objective_diagnosis_v8n/self_review.md`

## What Is Not Run
- no large DPO;
- no StageB;
- no GRPO;
- no full-data StageA;
- no broad-LoRA;
- no pair factory rollout;
- no new DPO-ready manifest;
- no videos pushed.
