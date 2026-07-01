Current Status:
PRD_READY_NOT_EXECUTED

# EXP Memory-Safe Winner-Anchor Diagnosis v8c

Updated: 2026-07-02 06:20 CST

This experiment follows `docs/experiments/PRD_VISUAL_AUDIT_POLICY.md`. It consumes already reviewed GT>C pairs from `manifests/dpo_smoke_v7_gt_c_10.jsonl` and does not create new DPO-ready pairs.

## Current Status

- v7 DPO smoke: engineering PASS, objective-signal FAIL.
- v8 sigma real-energy check: timeout before objective training.
- v8b sigma diagnosis: PASS for sampler-only and one-pair real-energy low/mid/high separation.
- v8b winner-anchor-only: OOM after 1 completed step of requested 5.
- Previous v8c attempt: connectivity-blocked on `hal-9000`; no experiment started and no repo files were changed there.

## Problem

Winner-anchor-only currently OOMs in the real training graph. The only completed v8b row had winner improvement 0.0, but that is not conclusive because only one step completed and the previous measurement did not do a robust post-update fresh energy recompute. The root cause may be measurement timing, memory leak, reference/policy graph overlap, full 81-frame activation cost, VAE encoding in the train path, retained loss tensors, or accidental loser branch work.

## Hypothesis

Winner-anchor-only should not need loser video or loser energy. It should not need reference participation during optimizer steps. E_ref_winner can be computed once under no_grad and cached. Winner latents can be precomputed so the training loop does not run VAE. With policy-only LoRA training, future-only latent masks, post-update no_grad recompute, gradient checkpointing where available, and temporal-window fallback if full81 OOMs, the 1-pair / 5-step gate should complete on a single GPU.

## Inputs

- Pair manifest: `manifests/dpo_smoke_v7_gt_c_10.jsonl`.
- Primary pair: first reviewed GT>C pair, `v6b_GT_C_001_01014_drop_orbit_left_72_seed40014`.
- v8b sigma artifacts:
  - `reports/dpo_objective_diagnosis_v8b/sigma_sampler_only.csv`
  - `reports/dpo_objective_diagnosis_v8b/sigma_real_energy_smoke.csv`
  - `reports/dpo_objective_diagnosis_v8b/winner_anchor_only_1pair_5step.csv`

## GPU Policy

- Use GPU4-7 only.
- Prefer physical GPU7 via `CUDA_VISIBLE_DEVICES=7`, so process-local `--gpu 0` maps to physical GPU7.
- Do not use physical GPU0-3.

## Method

1. Run a memory audit with staged GPU memory logging.
2. Implement a policy-only cached-latents winner-anchor runner.
3. Run 1-pair / 5-step winner-anchor-only.
4. Only if 1-pair passes, run 10-pair / 20-step winner-anchor-only.
5. Do not run strict SDPO, Linear-DPO, safe-linear, standard DPO, or checkpoint video eval in this round unless the explicit gates allow it.

## Metrics

- `E_ref_winner_cached`
- `E_policy_winner_pre_update`
- `E_policy_winner_post_update`
- `winner_improvement_pre`
- `winner_improvement_post`
- objective loss
- grad norm
- update norm
- LoRA parameter norm
- timestep / actual sigma
- used window frames
- allocated/reserved/max CUDA memory
- step time
- finite status and error reason

## Success Gate

- 1-pair 5-step completes.
- No OOM, SIGFPE, or NaN.
- Grad norm is nonzero.
- Update norm is positive.
- Post-update E_policy_winner decreases against cached reference.
- Final winner_improvement_post > 0.
- Mean winner_improvement_post > 0.

## Failure Gate

- OOM even after policy-only cached-latent config and one temporal-window fallback.
- Grad norm is zero.
- Update norm is zero.
- Post-update energy is unchanged or increases.
- Sigma, mask, or latent temporal mapping is inconsistent.
- finite=false.

## Output Paths

- `reports/dpo_objective_diagnosis_v8c/memory_audit.jsonl`
- `reports/dpo_objective_diagnosis_v8c/memory_audit_summary.md`
- `reports/dpo_objective_diagnosis_v8c/winner_anchor_only_1pair_5step.csv`
- `reports/dpo_objective_diagnosis_v8c/winner_anchor_only_1pair_summary.md`
- `reports/dpo_objective_diagnosis_v8c/winner_anchor_only_1pair_5step_window49.csv` if fallback is needed
- `reports/dpo_objective_diagnosis_v8c/winner_anchor_only_10pair_20step.csv` only if 1-pair passes
- `docs/dpo_objective_diagnosis_v8c_report.md`

## What Is Explicitly Not Run

- No standard DPO.
- No strict SDPO.
- No Linear-DPO.
- No safe-linear DPO.
- No large-scale DPO.
- No StageB.
- No GRPO.
- No full-data StageA.
- No broad-LoRA.
- No pair factory rollout.
- No checkpoint deletion.
- No MP4/JPG/PNG/checkpoint/weight push.

## Git Checkpoint

Commit before execution:

`Prepare memory-safe winner-anchor diagnosis v8c PRD`

A later commit will add the memory debug / runner and a final commit will record the actual v8c result.
