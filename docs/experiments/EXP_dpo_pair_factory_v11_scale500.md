<!-- RUN_RESULTS:START -->
Current Status: PAIR_FACTORY_V11_READY_500

## DPO Pair Factory v11 Scale-500

- Ready pairs: 500
- Train/val/test: 400 / 50 / 50
- Reviewed contact sheets: 931
- Source breakdown: `{'rollout_derived': 15, 'TypeA_plus': 3, 'synthetic_controlled': 482}`
- Data card: `docs/dpo_pair_factory_v11_data_card.md`
- Ready manifest: `manifests/dpo_pair_factory_v11_ready_500.jsonl`
- Caveat: controlled synthetic negatives dominate; real rollout DPO still needs rollout expansion.
- No DPO/training was run.
<!-- RUN_RESULTS:END -->

Current Status: PLANNED

# EXP: DPO Pair Factory v11 Scale-to-500

Generated: 2026-07-03 23:17:13

## Current Status

- v10b ready pairs = 81.
- Rollout-derived = 15.
- Synthetic controlled = 63.
- TypeA_plus = 3.
- Top50 balanced exists.
- Target now = 500 reviewed DPO-ready pairs.

## Problem

The current 81 pairs are not enough for the next DPO data gate. Real rollout-derived pairs remain limited, and future DPO work needs a larger, auditable mixed pool. Pair selection cannot rely only on reward/PSNR/SSIM: every ready pair must have contact sheet review and a written reason.

## Hypothesis

Using the existing 102+ runnable prefix5 conditions, controlled visible synthetic negatives, bounded real rollout attempts where available, strict contact sheet generation, metric/reward scoring, and Codex visual audit can produce 500 reviewed DPO-ready pairs.

## Pair Source Plan

1. Existing v10b strict ready: 81.
2. Controlled synthetic expansion: target 350-450 additional ready pairs.
3. Real rollout-derived expansion: target 50-100 if runtime allows.
4. Teacher/B/C pairs: optional and only if bounded rollout is safe.
5. Diagnostic rejected examples: retained for QA, not trainable.

## Inputs

- `manifests/dpo_pair_factory_v10b_ready_all.jsonl`
- `manifests/dpo_pair_factory_v10b_ready_rollout_only.jsonl`
- `manifests/dpo_pair_factory_v10b_ready_synthetic_controlled.jsonl`
- `manifests/dpo_pair_factory_v10b_top50_balanced.jsonl`
- `docs/dpo_pair_factory_v10b_report.md`
- `docs/dpo_pair_factory_v10b_data_card.md`
- `docs/next_real_rollout_pair_expansion_plan.md`

## Metrics

- Traditional: PSNR, SSIM, LPIPS if available, FVD if available, VBench if available.
- PhysGeo proxy: R_bg, R_cam, R_fg, R_phys, R_reobs, R_quality, P_freeze, P_blur, R_total.
- Quality: sharpness, blur, flicker, freeze_rate, brightness, contrast.

## Visual Audit Rule

No contact sheet means not ready. No written Codex visual review means not ready. No pair enters ready500 by reward-only, PSNR-only, SSIM-only, or metric-only selection.

## Success Gate

- >=500 reviewed DPO-ready pairs.
- Contact sheet coverage = 100% for ready pairs.
- Visual audit coverage = 100% for ready pairs.
- Train/val/test split = 400/50/50.
- Pair source clearly labels rollout-derived vs controlled synthetic vs TypeA_plus.
- No unreviewed loser enters ready manifest.

## Failure Gate

- <100 pairs: BLOCKED_INSUFFICIENT_PAIR_DATA.
- 100-499 pairs: PARTIAL_NOT_ENOUGH_FOR_DPO.
- Contact sheet coverage <100%.
- Visual audit coverage <100%.
- Any ready pair lacks written_reason.

## Outputs

- `manifests/dpo_pair_factory_v11_ready_500.jsonl`
- `manifests/dpo_pair_factory_v11_train400.jsonl`
- `manifests/dpo_pair_factory_v11_val50.jsonl`
- `manifests/dpo_pair_factory_v11_test50.jsonl`
- `manifests/dpo_pair_factory_v11_rollout_only.jsonl`
- `manifests/dpo_pair_factory_v11_synthetic_controlled.jsonl`
- `manifests/dpo_pair_factory_v11_top50_demo.jsonl`
- `reports/dpo_pair_factory_v11/`
- `docs/dpo_pair_factory_v11_report.md`
- `docs/dpo_pair_factory_v11_data_card.md`

## What Is Explicitly Not Run

- No DPO training.
- No SDPO.
- No Linear-DPO.
- No Safe-linear.
- No winner-anchor.
- No StageA / StageB / GRPO.
- No full-data long StageA.
- No broad-LoRA.
- No checkpoint deletion or checkpoint modification.
- No MP4/JPG/PNG/local_assets/checkpoint push.

## Git Checkpoint

- Before execution: commit PRD and v11 status.
- After each phase: commit/push lightweight source, manifests, summaries, and docs only.
