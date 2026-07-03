Current Status: MIXED

## 2026-07-04 Ready500 Loser Quality and Metrics Backend Update

- Re-audited all 500 v11 ready pairs for LOSE trainability.
- 497/500 are training-usable after loser quality audit.
- 3 TypeA_plus pairs are rejected/review-only due `too_subtle_metric`.
- Use `manifests/dpo_pair_factory_v11_ready500_trainable_after_loser_audit.jsonl` for any next tiny DPO data pass.
- LPIPS backend is now available and smoke-tested.
- FVD remains blocked by missing real temporal FVD backend/local I3D weights.
- VBench package/CLI is available but real scoring requires explicit project config and checkpoint/cache policy.

Current Status: PAIR_FACTORY_V11_READY_500

# DPO Pair Factory v11 Scale-500 Report

Generated: 2026-07-04 01:08:47

## Executive Summary

v11 expands the reviewed DPO preference-pair data asset from 81 ready pairs to exactly 500 selected DPO-ready pairs. A total of 931 contact sheets were generated and reviewed; 612 passed the DPO-ready visual gate, and 500 were selected with balancing constraints.

No DPO training, SDPO, Linear-DPO, winner-anchor, StageA, StageB, GRPO, or broad-LoRA was run.

## Counts

- Starting ready pairs: 81
- Generated synthetic candidates: 850 total attempted/generated across main+extra manifests
- Reviewed candidates/pairs: 931
- DPO-ready after audit: 612
- Final selected ready pairs: 500
- Train/val/test: 400 / 50 / 50

## Pair Source Breakdown

- Real rollout-derived: 15
- Controlled synthetic: 482
- TypeA_plus: 3

Important caveat: controlled synthetic negatives dominate v11. They are appropriate for anchored/controlled tiny DPO and LocalDPO-style experiments, but they are not real model rollout losers.

## Visual Audit

- Contact sheets: 931
- Reviewed: 931
- Ready before balancing: 612
- Rejected too subtle: 319
- Rejected too blurry: 0
- Rejected too easy: 0
- Rejected too artificial: 0
- Rejected collapsed: 0

## Metrics / Reward

- PSNR: PASS
- SSIM proxy: PASS
- PhysGeo proxy: PASS
- Quality floor: PASS for selected ready pairs
- LPIPS: BLOCKED_BY_ENV
- FVD: BLOCKED_BY_ENV
- VBench: BLOCKED_BY_ENV

## Manifests

- Ready500: `manifests/dpo_pair_factory_v11_ready_500.jsonl`
- Train400: `manifests/dpo_pair_factory_v11_train400.jsonl`
- Val50: `manifests/dpo_pair_factory_v11_val50.jsonl`
- Test50: `manifests/dpo_pair_factory_v11_test50.jsonl`
- Rollout-only: `manifests/dpo_pair_factory_v11_rollout_only.jsonl`
- Synthetic-only: `manifests/dpo_pair_factory_v11_synthetic_controlled.jsonl`
- Rejected: `manifests/dpo_pair_factory_v11_rejected.jsonl`

## PPT / QA

- Showcase MP4: `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v11_500_showcase.mp4`
- Selected CSV: `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v11_500_selected.csv`
- Notes: `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v11_500_notes.md`
- QA index: `reports/dpo_pair_factory_v11/qa_index.md`

## Decision

PAIR_FACTORY_V11_READY_500. This is enough for anchored tiny DPO data once the objective side is authorized. It is not enough to claim real rollout DPO is solved, because real rollout-derived pairs remain at 15. Next real rollout work should fix WanI2VFast/V2V-5 runtime expansion and target 50-100 rollout-derived pairs.


## Repaired Exact-500 Manifest

After the stricter loser audit, 3 original TypeA_plus pairs were marked review-only due `too_subtle_metric`. They were replaced from the already reviewed v11 candidate pool, producing an exact 500-row repaired manifest:

- `manifests/dpo_pair_factory_v11_ready_500_after_loser_audit_repaired.jsonl`
- Replacement summary: `reports/dpo_pair_factory_v11/loser_quality/ready500_repaired_manifest_summary.md`
- Replacement CSV: `reports/dpo_pair_factory_v11/loser_quality/ready500_replacement_pairs.csv`

Use this repaired manifest when an exact 500-pair training candidate set is required.
