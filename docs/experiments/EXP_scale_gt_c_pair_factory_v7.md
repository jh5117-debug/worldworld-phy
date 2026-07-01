# EXP Scale GT C Pair Factory v7

Current Status: PRD_READY_NOT_RUN

This experiment follows `docs/experiments/PRD_VISUAL_AUDIT_POLICY.md`.

## Goal

Expand reviewed GT>C DPO-ready medium-hard pairs from about 15 to at least 50 by running more prefix5 conditions through the B/C rollout pipeline.

## Hypothesis

C camera+self/temporal-r4 is currently the most promising medium-hard loser source. With more prefix5 conditions and two C seeds, it should yield more clear, readable, explainable losers without using blurred/collapsed negatives.

## Input Data

Primary condition input: `manifests/targeted_BC_loser_mining_v6b_conditions.jsonl`.

If fewer than 80 runnable conditions are available, recover more prefix5 conditions from existing manifests/reports/local_assets. Every condition must have prefix video, GT future video, GT full video, prompt, poses, intrinsics, template, camera_motion, prefix_len=5, and prediction_start_frame=5.

## Model / Checkpoint

- M0 Original Fast baseline, seed=1.
- M_B B camera-only rank8, seed=1, trainable params 13,107,200, role stable generator/control baseline.
- M_C C camera+self/temporal-r4, seeds=2, trainable params 1,310,720, role medium-hard loser source.
- Use only GPU4-7.

## Rollout Plan

Target 80 conditions:

- M0 seed=1
- B seed=1
- C seeds=2
- Expected videos: 80 * (1 + 1 + 2) = 320

If runtime is too long, run 40 conditions and mark `PARTIAL_40`.

## Metrics

For each rollout compute:

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

Unavailable LPIPS/FVD/VBench must be marked `BLOCKED_BY_ENV`; no fake substitutes.

## Loser Visual Audit Rule

Every C rollout loser must be reviewed via real video/contact sheet before it can enter a DPO-ready pair manifest. The experiment must emit:

- `reports/scale_gt_c_pair_factory_v7/loser_visual_audit.csv`
- `reports/scale_gt_c_pair_factory_v7/loser_visual_audit.jsonl`
- `reports/scale_gt_c_pair_factory_v7/loser_visual_audit_summary.md`
- `reports/scale_gt_c_pair_factory_v7/rejected_losers.csv`

No unreviewed loser may enter `manifests/dpo_gt_c_pairs_v7.jsonl` or `manifests/dpo_gt_c_pairs_v7_top50.jsonl`.

## Pair Selection Rule

Main pair: GT_C

- winner = clean GT future
- loser = C medium-hard rollout

Optional pair: B_C only if B absolute quality passes.

Keep only if:

- same prefix/prompt/poses/intrinsics;
- winner not bad;
- loser not collapsed;
- loser not too blurry;
- loser not too similar to GT;
- medium_hard = true;
- visual_quality_loser >= 1;
- sharpness_ok = true;
- reward_winner > reward_loser;
- preferred reward margin in [0.15, 0.35];
- preferred loser reward in [0.70, 0.85];
- Codex written_reason explains failure;
- subreward aligns with failure type;
- codex_visual_audit.reviewed = true;
- codex_visual_audit.is_dpo_ready = true.

## Success Gate

- >=50 DPO-ready reviewed GT>C pairs: `PAIR_FACTORY_V7_READY_FOR_SMALL_DPO`.
- >=10 but <50 DPO-ready reviewed GT>C pairs: `PAIR_FACTORY_V7_READY_FOR_TINY_SMOKE_ONLY`.
- <10 DPO-ready reviewed GT>C pairs: `BLOCKED_INSUFFICIENT_MEDIUM_HARD_PAIRS`.

## Failure Gate

Stop/diagnostic-only if rollout is blocked, visual audit is incomplete, too many losers are blurred/collapsed, C no longer yields medium-hard failures, or GPU4-7 are not safely available.

## Output Paths

- conditions: `manifests/scale_gt_c_pair_factory_v7_conditions_80.jsonl`
- condition summary: `reports/scale_gt_c_pair_factory_v7/condition_summary.csv`
- rollout root: `local_assets/scale_gt_c_pair_factory_v7/rollouts/`
- generated manifest: `reports/scale_gt_c_pair_factory_v7/generated_manifest.csv`
- generated JSONL: `reports/scale_gt_c_pair_factory_v7/generated_manifest.jsonl`
- rollout scores: `reports/scale_gt_c_pair_factory_v7/rollout_scores.csv`
- reward vectors: `reports/scale_gt_c_pair_factory_v7/reward_vectors.jsonl`
- video audit: `reports/scale_gt_c_pair_factory_v7/video_audit.csv`
- metric summary: `reports/scale_gt_c_pair_factory_v7/metric_summary.csv`
- pair manifest: `manifests/dpo_gt_c_pairs_v7.jsonl`
- top50 manifest: `manifests/dpo_gt_c_pairs_v7_top50.jsonl`
- pair audit: `reports/scale_gt_c_pair_factory_v7/pair_candidate_audit.csv`
- pair summary: `reports/scale_gt_c_pair_factory_v7/pair_summary.md`
- DPO-ready pairs: `reports/scale_gt_c_pair_factory_v7/dpo_ready_pairs_v7.jsonl`
- PPT video: `reports/ppt_winlose_showcase_latest/gt_c_pair_factory_v7_examples.mp4`
- report: `docs/scale_gt_c_pair_factory_v7_report.md`

## What Is Explicitly Not Run

No DPO training in this pair factory experiment, no StageB, no GRPO, no full-data long StageA, no broad-LoRA, no checkpoint deletion or modification, no data/weight/video push.

## Git Checkpoint

Before experiment commit: `Prepare SDPO smoke and GT-C pair factory v7 PRDs with visual audit policy`.
After experiment commit: `Scale GT-C pair factory v7 and document visual audit results`.
