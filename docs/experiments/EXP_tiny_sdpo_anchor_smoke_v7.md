# EXP Tiny SDPO Anchor Smoke v7

Current Status: PRD_READY_NOT_RUN

This experiment follows `docs/experiments/PRD_VISUAL_AUDIT_POLICY.md`.

## Goal

Run a tiny SDPO-anchor / winner-preserving DPO smoke on 8-10 reviewed GT>C medium-hard pairs. The goal is to test runtime and objective signal, not to claim quality improvement or scale DPO.

## Hypothesis

The current C rollout losers are medium-hard: their reward is high enough to avoid collapse/too-bad negatives, but lower than clean GT winner. SDPO-anchor should preserve the winner better than standard DPO-only updates.

## Input Data

Preferred source: `reports/targeted_BC_loser_mining_v6b/dpo_ready_pairs_v6b.jsonl`.
Fallback source: `manifests/dpo_typeB_C_loser_pairs_v6b.jsonl`.

Subset rule:

- 8-10 pairs.
- Prefer `pair_type = GT_C`.
- winner = clean GT future.
- loser = C camera+self/temporal-r4 rollout.
- loser reward between 0.70 and 0.85.
- reward margin between 0.15 and 0.35.
- visual_quality_loser >= 1.
- sharpness_ok = true.
- too_blurry = false.
- too_collapsed = false.
- medium_hard = true.
- `codex_visual_audit.reviewed = true` and `is_dpo_ready = true`.
- Cover drop, collision, roll, containment when possible.

## Model / Checkpoint

- Base model: LingBot-Fast V2V-5.
- DPO trainable scope: camera-conditioning LoRA rank4 unless the existing DPO trainer config requires its previous smoke scope.
- Reference: frozen.
- Precision: BF16 mixed-safe, VAE FP32.
- Condition: prefix frames 0-4, future frames 5-80 scored.
- Future-only loss: required.
- Same noise and same timestep: required.

## Objective

SDPO-anchor / winner-preserving:

`L_total = L_safe_DPO + lambda_w * E_policy_winner`

Track:

- lambda_loser
- lambda_w
- dpo_loss
- anchor_loss
- total_loss
- winner_improvement
- loser_degradation
- winner_contribution_ratio
- Delta_policy
- Delta_ref
- reference_relative_margin
- grad_norm
- update_norm
- lr
- sigma
- timestep
- actual_sigma_bin
- GPU memory
- step time

Rules:

- If winner_improvement <= 0, lambda_loser = 0.0 or 0.25.
- If winner_contribution_ratio < 0.30, lambda_loser = 0.25.
- No standard DPO-only scale.

## Metrics

- DPO loss
- implicit accuracy
- winner_improvement
- loser_degradation
- winner_contribution_ratio
- PSNR
- SSIM
- LPIPS if available
- FVD if available
- VBench if available
- PhysGeo reward
- sharpness / blur
- freeze
- Codex visual audit for checkpoint rollouts

Unavailable LPIPS/FVD/VBench must be marked `BLOCKED_BY_ENV`; no substitute metric may be faked.

## Loser Visual Audit Rule

All subset losers must already be reviewed under `docs/experiments/PRD_VISUAL_AUDIT_POLICY.md`. The experiment must emit:

- `reports/dpo_smoke_v7/loser_visual_audit.csv`
- `reports/dpo_smoke_v7/loser_visual_audit.jsonl`
- `reports/dpo_smoke_v7/loser_visual_audit_summary.md`

If the audit is incomplete, status becomes `BLOCKED_VISUAL_AUDIT_INCOMPLETE` and DPO smoke must not start.

## Success Gate

Engineering pass requires:

- no OOM / SIGFPE / NaN;
- reference frozen;
- same noise / same timestep;
- future-only loss;
- checkpoint save/load;
- max 20 optimizer steps;
- step0 / step5 / step10 / step20 checkpoints or documented skipped optional step20;
- real V2V-5 checkpoint videos generated;
- metrics computed or blocked honestly;
- Codex visual audit completed.

Objective signal does not need to be positive, but unhealthy signal must be labeled and not scaled.

## Failure Gate

Mark failure/no-scale if:

- runtime error, OOM, NaN, SIGFPE;
- winner_improvement < 0;
- winner_contribution_ratio < 0.30;
- video quality degrades;
- hallucinated fragments increase;
- freeze increases;
- DPO loss is driven only by loser degradation.

## Output Paths

- subset: `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- subset summary: `reports/dpo_smoke_v7/subset_summary.csv`
- run root: `local_assets/dpo_smoke_v7_<timestamp>/`
- training metrics: `reports/dpo_smoke_v7/training_metrics.csv`
- checkpoint inventory: `reports/dpo_smoke_v7/checkpoint_inventory.csv`
- signal summary: `reports/dpo_smoke_v7/dpo_signal_summary.csv`
- BF16 runtime: `reports/dpo_smoke_v7/bf16_runtime.csv`
- decision: `reports/dpo_smoke_v7/smoke_decision.json`
- video audit: `reports/dpo_smoke_v7/video_audit.csv`
- checkpoint eval summary: `reports/dpo_smoke_v7/checkpoint_eval_summary.csv`
- PSNR/SSIM/LPIPS: `reports/dpo_smoke_v7/psnr_ssim_lpips.csv`
- PhysGeo metrics: `reports/dpo_smoke_v7/physgeo_metrics.csv`
- PPT video: `reports/ppt_winlose_showcase_latest/dpo_smoke_v7_checkpoint_comparison.mp4`
- report: `docs/dpo_smoke_v7_report.md`

## What Is Explicitly Not Run

No large-scale DPO, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, checkpoint modification, or data/weight push.

## Git Checkpoint

Before experiment commit: `Prepare SDPO smoke and GT-C pair factory v7 PRDs with visual audit policy`.
After experiment commit: `Run tiny SDPO-anchor DPO smoke v7`.
