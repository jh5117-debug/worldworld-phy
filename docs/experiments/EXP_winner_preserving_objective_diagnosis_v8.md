Current Status:
BLOCKED

## Actual Result 2026-07-02

- PRD was committed and pushed before execution.
- Full real-energy sigma-bin check was attempted on `manifests/dpo_smoke_v7_gt_c_10.jsonl` with 10 reviewed GT>C pairs.
- GPU: physical GPU4 only.
- Runtime: stopped after the 60 minute safety window.
- Evidence: latent precompute completed and 16 checkpoint shards loaded; GPU4 stayed saturated in the energy loop, but no actual sigma/energy CSV rows were produced.
- Status: `SIGMA_ENERGY_CHECK_TIMEOUT`.
- Winner-anchor-only: NOT_RUN.
- Strict SDPO-anchor: NOT_RUN.
- Linear-DPO + winner-anchor: NOT_RUN.
- SDPO + linear utility: NOT_RUN.
- Decision: `OBJECTIVE_BLOCKED_SIGMA_ENERGY_CHECK_TIMEOUT`; do not run objective training until sigma mapping has a bounded/progress-writing check.

# EXP Winner-Preserving Objective Diagnosis v8

Updated: 2026-07-01 23:25 CST

This experiment follows `docs/experiments/PRD_VISUAL_AUDIT_POLICY.md`.

## Current Status

Tiny SDPO-anchor DPO smoke v7 completed on 10 reviewed GT>C medium-hard pairs. Runtime was engineering-positive, but the objective signal failed:

- steps: 20 / 20
- final DPO loss: 0.693138
- final winner improvement: -0.0002627
- final loser degradation: 0.0004442
- final winner contribution ratio: 0.0
- decision: `ENGINEERING_PASS_OBJECTIVE_SIGNAL_FAIL`

Checkpoint videos at step0 / step5 / step10 / step20 were generated and reviewed. Step10 had the best PSNR/SSIM in the one-sample smoke, but visual quality remained poor and step20 increased hallucinated fragments. The current SDPO-anchor objective must not be scaled or repeated as-is.

## Goal

Diagnose whether a winner-preserving objective can directly reduce winner energy before any loser-driven preference term is allowed to dominate. This is a tiny objective diagnosis only, not a scale-up run.

## Hypothesis

The v7 failure may come from the safe-DPO term and loser-side update overwhelming the winner anchor. A winner-anchor-only probe should answer the first necessary question: can the current LoRA scope and energy backend reduce `E_policy_winner` relative to the frozen reference on the same reviewed GT>C subset?

If winner-anchor-only cannot improve the winner, then stricter SDPO or linear-DPO variants are not meaningful yet and the next fix should target the energy backend, sigma schedule, LoRA scope, or winner latent monitor.

## Input Pairs

- Pair subset: `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- Pair type: reviewed GT>C medium-hard pairs
- Pair count: 10
- Winner: clean GT future
- Loser: C camera+self-temporal-r4 medium-hard rollout
- Required audit: every loser must have `codex_visual_audit.reviewed = true` and `is_dpo_ready = true`
- Frames: prefix frames 0-4 as condition, future frames 5-80 as target/reward/loss region

## Model / Checkpoint

- Base model: LingBot-Fast V2V-5
- Policy LoRA: camera-conditioning rank4 baseline unless the existing DPO trainer requires the v7 smoke scope
- Reference: frozen copy of the same base/checkpoint
- Precision: BF16 mixed-safe, VAE FP32
- Authorized GPUs: physical GPU4-7 only unless explicitly blocked
- No broad-LoRA, no FFN, no StageB, no full-data StageA

## Sigma / Timestep Precheck

Before objective training, run an energy-only sigma-bin check on the same 10 pairs for requested bins:

- low
- mid
- high

Record `requested_bin`, `timestep`, and `actual_sigma`. If all bins map to the same sigma, mark `SIGMA_MAPPING_BROKEN`, stop objective training, and fix the sampler before claiming any objective result is complete.

Outputs:

- `reports/dpo_objective_diagnosis_v8/sigma_bin_check.csv`
- `reports/dpo_objective_diagnosis_v8/sigma_bin_check.md`

## Objectives

Run at most 20 optimizer steps per objective, in this order:

1. `winner_anchor_only`
   - loss = `E_policy_winner`
   - `lambda_loser = 0`
   - Goal: prove winner energy can be reduced.

2. `strict_sdpo_anchor`
   - `L = L_DPO_safe + lambda_w * E_policy_winner`
   - `lambda_loser = 0` until `winner_improvement > 0` for 3 consecutive eval steps, then `lambda_loser = 0.25`.

3. `linear_dpo_anchor`
   - `u = Delta_policy - Delta_ref`
   - `L = - pair_weight * clamp(u, -u_clip, u_clip) + lambda_w * E_policy_winner`
   - `pair_weight` comes from reward margin.

4. `safe_linear_dpo`
   - Combine the safe loser schedule with the linear utility term.

If `winner_anchor_only` fails, stop B/C/D early and write `OBJECTIVE_BLOCKED_WINNER_ANCHOR_FAIL`.

## Metrics

For every step record:

- dpo_loss or objective_loss
- winner_anchor_loss
- E_policy_winner
- E_ref_winner
- E_policy_loser
- E_ref_loser
- winner_improvement
- loser_degradation
- winner_contribution_ratio
- lambda_loser
- lambda_w
- Delta_policy
- Delta_ref
- u
- sigma
- actual_sigma_bin
- grad_norm
- update_norm
- GPU memory
- step_time

For checkpoint video eval, compute PSNR, SSIM, LPIPS if available, PhysGeo if available, and FVD/VBench if available. Missing FVD/VBench must be recorded as `BLOCKED_BY_ENV`.

## Visual Audit Requirement

Checkpoint video eval is required only for the best objective that passes runtime and shows a non-blocked signal. Generate V2V-5 videos at step0 / step5 / step10 / step20 and Codex must inspect all contact sheets before any objective is considered visually usable.

Outputs:

- `reports/dpo_objective_diagnosis_v8/video_audit.csv`
- `reports/dpo_objective_diagnosis_v8/checkpoint_eval_summary.csv`

## Success Gate

An objective is signal-positive only if:

- mean winner_improvement > 0
- winner_contribution_ratio >= 0.30
- not dominated by loser_degradation
- no OOM / SIGFPE / NaN
- reference frozen true
- save/load OK
- sigma bins are not collapsed to one actual sigma

## Failure Gate

Mark blocked or failed if:

- sigma mapping collapses low/mid/high bins to the same actual sigma
- winner-anchor-only cannot improve winner energy
- final winner_improvement is negative
- winner_contribution_ratio remains near 0
- loser_degradation is the only meaningful signal
- checkpoint videos become visually worse or hallucinated fragments increase

## Output Paths

- root: `reports/dpo_objective_diagnosis_v8/`
- winner-anchor-only: `reports/dpo_objective_diagnosis_v8/winner_anchor_only.csv`
- strict SDPO: `reports/dpo_objective_diagnosis_v8/strict_sdpo_anchor.csv`
- linear DPO anchor: `reports/dpo_objective_diagnosis_v8/linear_dpo_anchor.csv`
- safe linear DPO: `reports/dpo_objective_diagnosis_v8/safe_linear_dpo.csv`
- objective summary: `reports/dpo_objective_diagnosis_v8/objective_summary.csv`
- decision: `reports/dpo_objective_diagnosis_v8/decision.json`
- report: `docs/dpo_objective_diagnosis_v8_report.md`

## What Is Explicitly Not Run

No large DPO, no StageB, no GRPO, no full-data StageA, no broad-LoRA, no checkpoint deletion, no checkpoint overwrite, no data/weight/video push, and no unreviewed loser is allowed into any manifest.

## Git Checkpoint

- Before execution commit: `Prepare winner-preserving DPO diagnosis v8 PRDs`
- After execution commit: `Diagnose winner-anchor and safe DPO objectives`
