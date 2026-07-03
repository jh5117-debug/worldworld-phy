Current Status: PLANNED

# EXP: v11 Ready500 Loser Quality Audit and Metrics Backend Repair

Generated: 2026-07-04 03:35:55

## Current Status

- DPO Pair Factory v11 ready500 exists.
- `manifests/dpo_pair_factory_v11_ready_500.jsonl` has 500 reviewed pairs.
- Every pair has a contact sheet path and Codex visual audit from v11.
- Metrics status still has LPIPS/FVD/VBench as BLOCKED_BY_ENV.

## Problem

The ready500 data asset must be checked pair-by-pair before training. In particular, every LOSE must be readable, not collapsed, not too blurry, not too artificial for the intended controlled/anchored objective, and must have a concrete failure reason. Also, LPIPS/FVD/VBench backends should be repaired if possible without sudo, huge downloads, or destructive changes.

## Hypothesis

A dedicated loser-quality audit over the 500 contact sheets and loser videos can separate trainable pairs from any diagnostic-only pairs. LPIPS may be fixable by a small Python dependency. FVD/VBench may require heavier model weights; if so, the exact blocker must be documented rather than faked.

## Inputs

- `manifests/dpo_pair_factory_v11_ready_500.jsonl`
- `reports/dpo_pair_factory_v11/contact_sheet_manifest_all.csv`
- `reports/dpo_pair_factory_v11/scoring/pair_scores.csv`
- `reports/dpo_pair_factory_v11/visual_audit/pair_visual_audit.csv`

## Outputs

- `reports/dpo_pair_factory_v11/loser_quality/ready500_loser_quality_audit.csv`
- `reports/dpo_pair_factory_v11/loser_quality/ready500_loser_quality_audit.jsonl`
- `reports/dpo_pair_factory_v11/loser_quality/ready500_loser_quality_summary.md`
- `manifests/dpo_pair_factory_v11_ready500_trainable_after_loser_audit.jsonl`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/metrics_backend_status.csv`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/metrics_backend_status.md`

## Success Gate

- 500/500 rows audited.
- Every retained training pair has trainable_after_loser_audit=true.
- LPIPS import/smoke fixed if possible.
- FVD/VBench either PASS or exact blocker documented.

## What Is Not Run

No DPO, no training, no SDPO, no Linear-DPO, no winner-anchor, no StageA/StageB/GRPO, no checkpoint modifications.


## Result Update


### 2026-07-04 04:10:15

- Ready500 loser quality audit completed for 500/500 rows.
- 497 pairs remain training-usable after stricter loser audit.
- 3 TypeA_plus pairs are marked `REJECT_OR_REVIEW` due `too_subtle_metric`.
- LPIPS backend repaired and real alex smoke passed.
- FVD remains blocked by missing real temporal FVD backend/local I3D weights; image FID is not substituted.
- VBench package and CLI are available, but actual scoring is blocked until project-local dimensions, input folder convention, and checkpoint/cache policy are configured.
- No DPO/training/StageA/StageB/GRPO was run.
