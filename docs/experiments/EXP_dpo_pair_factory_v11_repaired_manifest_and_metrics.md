Current Status: STARTED

# EXP: DPO Pair Factory v11 Repaired Manifest and Metrics Backend Verification

Generated: 2026-07-04 11:46:48

## Current Status

- Ready500 was repaired after loser-quality audit.
- 497 original rows passed the stricter loser audit.
- 3 TypeA_plus rows were rejected as `too_subtle_metric` and replaced.
- Canonical manifest should now be the repaired one: `manifests/dpo_pair_factory_v11_ready_500_after_loser_audit_repaired.jsonl`.
- Metrics backend is partially repaired: LPIPS passes; VBench CLI imports; FVD remains blocked.

## Problem

- The old ready500 manifest should no longer be used as the training entry because it contains 3 too-subtle pairs.
- VBench import/CLI help is not equivalent to verified VBench scoring.
- FVD is still not available as a real video metric.
- Metric environment may conflict with future rollout/training because VBench install changed user-site `transformers` to 4.33.2 while fastwam expects 4.49.0.

## Goal

- Freeze the repaired manifest as canonical.
- Regenerate train400 / val50 / test50 / top50 demo splits from the repaired manifest.
- Run a small real LPIPS metric smoke using actual LPIPS model outputs.
- Run a small VBench real scoring smoke if possible, or document exact weights/cache/config blocker.
- Audit FVD honestly and refuse image-FID-as-FVD substitution.

## Inputs

- `manifests/dpo_pair_factory_v11_ready_500.jsonl`
- `manifests/dpo_pair_factory_v11_ready_500_after_loser_audit_repaired.jsonl`
- `reports/dpo_pair_factory_v11/loser_quality/ready500_loser_quality_audit.csv`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/metrics_backend_status.md`

## Metrics

- Pair counts and source/failure breakdowns.
- SHA256 of canonical and split manifests.
- LPIPS winner-vs-loser for 10 representative pairs.
- VBench real scoring smoke status and exact blocker if not runnable.
- FVD import/backend/weight audit status.

## Success Gate

- Canonical repaired manifest has exactly 500 rows.
- Removed too-subtle pair IDs are absent.
- Replacement pair IDs are present.
- Repaired train400/val50/test50/top50 are generated without duplicate pair IDs.
- LPIPS real metric smoke produces numeric rows.
- VBench and FVD statuses are honest and reproducible.

## Failure Gate

- Repaired manifest count is not 500.
- Removed too-subtle IDs remain present.
- LPIPS fails to load the real model.
- VBench needs unauthorized large downloads or missing local cache.
- FVD has no local temporal backend/weights.

## Output Paths

- `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- `manifests/dpo_pair_factory_v11_train400_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_val50_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_test50_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_top50_demo_repaired.jsonl`
- `reports/dpo_pair_factory_v11/repaired_freeze/`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/`
- `docs/dpo_pair_factory_v11_repaired_ready500_report.md`

## What Is Not Run

- No training.
- No DPO / SDPO / Linear-DPO / winner-anchor.
- No checkpoint changes.
- No video or image push.
- No StageA / StageB / GRPO.
