Current Status:
PASS

## 2026-07-03T09:15:05 Result Update

- Decision: `CACHE10_VALIDATED_PASS`.
- Build: 10/10 cache rows PASS.
- Validation: 10/10 PASS.
- Validator patched to enforce true no-loser-field gate.
- Next action: v8k cache-only 10-pair winner-anchor diagnosis.

Current Status:
READY_TO_RUN

# EXP Cache10 After Runtime Ready v8j

Updated: 2026-07-03T08:50:49

## Current Status

- v8i PASS: `ENSURE_RUNTIME_READY_PASS_FIRST_ROW_PASS`.
- Safe Wan policy loader reaches runtime ready.
- Full-condition one-pair minimal cache row was written with `diagnostic_skip_text=False` and `diagnostic_skip_vae=False`.
- T5 checkpoint fast-init patch is applied in cache builder before runtime readiness.

## Problem

The one-pair first-row cache path is now valid, but cache10 has not yet been built or validated. DPO/SDPO/Linear-DPO must remain blocked until cache10 validates and later cache-only winner-anchor passes.

## Hypothesis

With the safe Wan loader and T5 fast-init patch, reusable cache build can process 10 reviewed GT>C pairs one at a time, write incremental rows, include scalar reference winner energy, and validate without loading losers or running training.

## Inputs

- `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- v8i code path in `cam_physgeo/dpo/winner_anchor_cache_builder.py`
- v8i first-row evidence under `reports/dpo_objective_diagnosis_v8i/`

## GPU

- H20 physical GPU4-7 only.
- Prefer physical GPU7 via `CUDA_VISIBLE_DEVICES=7`, process `--gpu 0`.
- Do not use GPU0-3.

## Plan

1. Build 10-pair cache with `cache_level=with_ref_energy`.
2. Write pair rows incrementally.
3. Validate cache files, shapes, finite tensors, prefix/future settings, no loser fields, and scalar `E_ref_winner_cached`.
4. If builder hits a code/schema blocker, patch non-destructively and rerun within bounded attempts.

## Success Gate

- Cache build success >= 8 pairs, preferred 10/10.
- Cache validation PASS for successful rows.
- No DPO / SDPO / Linear-DPO / training run.
- No hidden prefix_len=1 or image-only fallback.

## Failure Gate

- Cache build writes zero rows.
- Cache validation fails for schema/finite/shape reasons that cannot be patched safely.
- GPU4-7 unavailable.
- Destructive operation required.

## Output Paths

- `local_assets/dpo_objective_cache_v8j/gt_c_10_window49/`
- `reports/dpo_objective_diagnosis_v8j/cache_build_10pair_with_ref.csv`
- `reports/dpo_objective_diagnosis_v8j/cache_validation_10pair.csv`
- `reports/dpo_objective_diagnosis_v8j/self_review.md`
- `docs/dpo_objective_diagnosis_v8j_report.md`

## What Is Not Run

- no DPO
- no SDPO
- no Linear-DPO
- no cache-only winner-anchor training in this PRD phase
- no pair factory rollout
- no StageB / GRPO / full-data StageA / broad-LoRA
