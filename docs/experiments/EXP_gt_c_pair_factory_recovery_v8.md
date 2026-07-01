Current Status:
PRD_READY_NOT_STARTED

# EXP GT>C Pair Factory Recovery v8

Updated: 2026-07-01 23:25 CST

This experiment follows `docs/experiments/PRD_VISUAL_AUDIT_POLICY.md`.

## Current Status

GT>C pair factory v7 did not launch a new large rollout window. It recovered only 21 runnable prefix5 conditions toward the 80-condition target, while the v7 tiny DPO smoke used the existing 10 reviewed GT>C pairs. Current DPO-ready scale remains too small for anything beyond tiny smoke.

Known usable source before v8:

- `manifests/dpo_smoke_v7_gt_c_10.jsonl`: 10 reviewed GT>C pairs used for v7 smoke
- `manifests/dpo_typeB_C_loser_pairs_v6b.jsonl`: v6b reviewed GT>C pool
- `manifests/targeted_BC_loser_mining_v6b_conditions.jsonl`: recovered prefix5 condition source

## Goal

Recover or build at least 80 runnable prefix5 conditions, then run the B/C rollout pair factory to produce a larger reviewed GT>C pool. The target is >=50 DPO-ready reviewed GT>C pairs, but this experiment does not train DPO.

## Hypothesis

The current bottleneck is pair quantity, not v7 runtime plumbing. B camera-r8 is stable enough as a control/candidate generator, and C camera+self-temporal-r4 is the best current medium-hard loser source. With more runnable prefix5 conditions and C seed diversity, the factory should produce more clear, non-collapsed medium-hard GT>C losers.

## Input Data

Read first:

- `manifests/targeted_BC_loser_mining_v6b_conditions.jsonl`
- `reports/targeted_BC_loser_mining_v6b/runnable_condition_check.csv`
- `reports/targeted_BC_loser_mining_v6b/runnable_condition_summary.md`

If only 21 conditions exist, recover more from available manifests, existing full videos, or quant benchmark rows. If needed, cut prefix frames 0-4 and GT future frames 5-80 from existing full videos. Every condition must include:

- condition_id
- prefix video with 5 decodable frames
- GT future video with 76 decodable frames
- prompt or prompt path
- poses.npy with finite values
- intrinsics.npy with finite values
- gt_full_video_path
- template and camera_motion metadata when available

## Model / Checkpoint

- M0: Original Fast baseline, seed=1
- M_B: B camera-only rank8, seed=1, stable generator/control baseline, trainable params 13,107,200
- M_C: C camera+self-temporal-r4, seeds=2, medium-hard loser source, trainable params 1,310,720
- Authorized GPUs: physical GPU4-7 only unless explicitly blocked
- No broad-LoRA, no training update, no checkpoint modification

## Rollout Plan

1. Recover/validate condition manifest.
2. Run 40 conditions first if recovered conditions allow.
3. Run 80 conditions only if the 40-condition stage succeeds.

Expected videos for 80 conditions:

- M0 seed1: 80 videos
- B seed1: 80 videos
- C seed2: 160 videos
- total: 320 videos

If GPU/time is insufficient, stop at 40 conditions and mark partial rather than forcing an uncontrolled long rollout.

## Metrics

For every rollout compute or explicitly block:

- PSNR
- SSIM
- LPIPS if available
- FVD if available
- VBench if available
- R_bg
- R_cam
- R_fg
- R_phys
- R_reobs
- R_quality
- P_freeze
- P_blur
- R_total
- sharpness
- blur
- flicker
- freeze_rate

FVD/VBench must remain `BLOCKED_BY_ENV` if the backend is unavailable; no fake substitute is allowed.

## Visual Audit Requirement

Every C rollout loser must have a contact sheet and Codex visual review before it enters any DPO-ready manifest. Required outputs:

- `reports/scale_gt_c_pair_factory_v8/loser_visual_audit.csv`
- `reports/scale_gt_c_pair_factory_v8/loser_visual_audit.jsonl`
- `reports/scale_gt_c_pair_factory_v8/rejected_losers.csv`

Reject losers that are too blurry, collapsed, black screen, too similar to winner, too bad, or lack an explainable failure.

## Pair Selection Rule

Main pair:

- pair type: GT_C
- winner = clean GT future
- loser = C medium-hard rollout

Optional pair:

- B_C only if B absolute quality passes and is visually a valid winner.

Every kept pair must satisfy:

- same prefix/prompt/poses/intrinsics
- winner not bad
- loser not collapsed
- loser not too blurry
- loser not too similar to winner
- medium_hard = true
- reward_winner > reward_loser
- subreward aligns with failure type
- Codex written reason is present
- `codex_visual_audit.reviewed = true`

## Success Gate

- DPO-ready >=50: `PAIR_FACTORY_READY_FOR_SMALL_DPO`
- DPO-ready >=10 and <50: `READY_FOR_TINY_ONLY`
- DPO-ready <10: `BLOCKED_INSUFFICIENT_PAIRS`

## Failure Gate

Mark blocked if runnable conditions remain below 40, rollout runner is unavailable, GPU4-7 are not safely available, visual audit is incomplete, or most C rollouts are blurry/collapsed/too similar.

## Output Paths

- condition manifest: `manifests/scale_gt_c_pair_factory_v8_conditions.jsonl`
- rollout root: `local_assets/scale_gt_c_pair_factory_v8/rollouts/`
- generated manifest: `reports/scale_gt_c_pair_factory_v8/generated_manifest.csv`
- metrics: `reports/scale_gt_c_pair_factory_v8/metric_summary.csv`
- loser audit: `reports/scale_gt_c_pair_factory_v8/loser_visual_audit.csv`
- rejected losers: `reports/scale_gt_c_pair_factory_v8/rejected_losers.csv`
- all pairs: `manifests/dpo_gt_c_pairs_v8.jsonl`
- top50: `manifests/dpo_gt_c_pairs_v8_top50.jsonl`
- pair summary: `reports/scale_gt_c_pair_factory_v8/pair_summary.md`
- report: `docs/scale_gt_c_pair_factory_v8_report.md`

## What Is Explicitly Not Run

No DPO training, no large DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA, no checkpoint deletion or modification, no unreviewed loser in a manifest, and no data/weight/video push.

## Git Checkpoint

- Before execution commit: `Prepare winner-preserving DPO diagnosis v8 PRDs`
- After execution commit: `Recover GT-C pair factory v8 and document results`
