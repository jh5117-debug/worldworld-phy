Current Status:
READY_TO_RUN

# EXP Cache10 Winner-Anchor v8k

Updated: 2026-07-03T09:16:56

## Current Status

- v8i first-row full-condition cache PASS.
- v8j cache10 build PASS: 10/10 rows.
- v8j cache validation PASS: 10/10 rows.
- Cache root: `local_assets/dpo_objective_cache_v8j/gt_c_10_window49`.

## Problem

v8c proved 1-pair/window49 winner-anchor can produce positive post-update winner improvement, but 10-pair winner-anchor has not yet completed from reusable cache.

## Hypothesis

Cache-only policy training removes repeated VAE/T5/reference cache bottlenecks. If objective sign, mask, sigma, and LoRA scope are correct, 10-pair 20-step winner-anchor-only should complete without OOM and produce positive mean/final winner_improvement_post.

## Inputs

- `local_assets/dpo_objective_cache_v8j/gt_c_10_window49`
- `manifests/dpo_smoke_v7_gt_c_10.jsonl` provenance, reviewed GT>C pairs only.

## GPU

- H20 physical GPU4-7 only.
- Prefer GPU7 via `CUDA_VISIBLE_DEVICES=7`, process `--gpu 0`.
- Do not use GPU0-3.

## Command

`python -m cam_physgeo.dpo.winner_anchor_only_runner --cache_root local_assets/dpo_objective_cache_v8j/gt_c_10_window49 --num_pairs 10 --steps 20 --gpu 0 --mode cache_only_policy_train`

## Success Gate

- 20 steps complete.
- No OOM / NaN / SIGFPE.
- Nonzero grad and update_norm > 0.
- Mean winner_improvement_post > 0.
- Final winner_improvement_post > 0.

## Failure Gate

- OOM.
- Grad zero or update_norm zero.
- Mean/final winner_improvement_post <= 0.
- Cache-only path secretly loads loser/reference/VAE/T5 in the training loop.

## Output Paths

- `reports/dpo_objective_diagnosis_v8k/winner_anchor_cache10_20step.csv`
- `reports/dpo_objective_diagnosis_v8k/winner_anchor_cache10_20step_summary.md`
- `docs/dpo_objective_diagnosis_v8k_report.md`

## What Is Not Run

- no DPO
- no SDPO
- no Linear-DPO
- no Safe-linear
- no large DPO
- no StageB / GRPO / full-data StageA / broad-LoRA
