Current Status:
PLANNED_REUSABLE_CACHE_WINNER_ANCHOR_V8D

# EXP Reusable Cache Winner-Anchor Diagnosis v8d

Updated: 2026-07-02 09:18 CST

This experiment follows docs/experiments/PRD_VISUAL_AUDIT_POLICY.md. It consumes already reviewed GT>C pairs from manifests/dpo_smoke_v7_gt_c_10.jsonl and does not create new DPO-ready pairs.

## Current Status

- v7 DPO smoke: engineering PASS, objective-signal FAIL.
- v8b sigma diagnosis: sampler-only and one-pair real-energy PASS; sigma mapping is separated.
- v8c 1-pair/window49 winner-anchor-only: PASS with final winner_improvement_post = +6.324e-05.
- v8c 10-pair / 20-step: blocked before optimizer because cache/precompute was too slow.

## Problem

The 10-pair winner-anchor training run cannot start reliably because cache construction is too slow. The current path may repeatedly run VAE encoding, condition packing, text/control preparation, and reference-energy computation before training. This prevents deciding whether winner-anchor-only works beyond one pair.

## Hypothesis

If all pair-level inputs are precomputed into reusable cache files, then 10-pair winner-anchor-only can complete 20 optimizer steps without OOM or cache bottleneck. The training step should load cached tensors, avoid VAE and reference work, train only LoRA parameters, and report whether post-update winner energy decreases.

## Inputs

- Reviewed pair subset: manifests/dpo_smoke_v7_gt_c_10.jsonl
- Window: 49 frames
- Prefix length: 5
- Prediction start frame: 5

## GPU Policy

- Use GPU4-7 only.
- Prefer physical GPU7 via CUDA_VISIBLE_DEVICES=7, so process-local --gpu 0 maps to physical GPU7.
- Do not use physical GPU0-3.

## Method

1. Build reusable cache one pair at a time.
2. Persist winner latents, target/noisy latent, text context, control tensors, future-only mask, timestep/sigma metadata, and E_ref_winner.
3. Validate cache integrity, shape, dtype, finite values, hashes, no loser fields, prefix_len=5, prediction_start_frame=5, used_window_frames=49.
4. Run cache-only 10-pair / 20-step winner-anchor-only.
5. Do not run strict SDPO, Linear-DPO, safe-linear, standard DPO, or pair-factory rollout in this round.

## Metrics

- Cache build success/failure count
- Cache validation pass/fail count
- E_ref_winner_cached
- E_policy_winner_pre_update
- E_policy_winner_post_update
- winner_improvement_pre / winner_improvement_post
- loss, grad norm, update norm, LoRA param norm
- timestep / actual sigma
- used window frames
- CUDA memory and step time
- finite status and error reason

## Success Gate

- 10-pair cache completes.
- Cache validates.
- 10-pair winner-anchor enters optimizer loop and completes 20 steps.
- No OOM / SIGFPE / NaN.
- Nonzero grad and update_norm > 0.
- Mean and final winner_improvement_post > 0.

## Failure Gate

- Cache precompute exceeds time limit or fewer than 10 pairs succeed.
- Cache invalid.
- OOM / SIGFPE / NaN.
- Grad or update norm zero.
- Post-update winner energy does not decrease.
- Cache silently falls back to image-only or prefix_len=1.

## Output Paths

- Cache root: local_assets/dpo_objective_cache_v8d/gt_c_10_window49/
- Reports: reports/dpo_objective_diagnosis_v8d/
- Main CSV: reports/dpo_objective_diagnosis_v8d/winner_anchor_cache10_20step.csv

## What Is Explicitly Not Run

No SDPO, Linear-DPO, safe-linear DPO, DPO scale, pair factory rollout, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or video/weight push.

## Git Checkpoints

- Commit PRD before execution.
- Commit source/tests after cache builder and validator implementation.
- Commit final docs/reports after v8d run.
