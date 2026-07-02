Current Status:
PLANNED_REUSABLE_CACHE_WINNER_ANCHOR_V8D

# DPO Objective Diagnosis v8d Status

Updated: 2026-07-02 09:18 CST

## Current State

- v7 tiny SDPO-anchor DPO smoke was engineering-stable but objective-signal failed; do not scale.
- v8b sigma sampler-only and real-energy smoke passed; sigma/timestep mapping is no longer the blocker.
- v8c proved 1-pair/window49 winner-anchor-only can run memory-safe and produce positive post-update winner improvement.
- v8c full81 was too slow and winner-negative after 2/5 steps.
- v8c 10-pair expansion did not enter optimizer steps because multi-pair VAE/cache construction was too slow.

## Active Blocker

The blocker is reusable precompute/cache, not sigma mapping. The 10-pair winner-anchor gate cannot be trusted until the training loop stops repeatedly running VAE, condition packing, and reference-energy setup.

## v8d Goal

Build a reusable cache for the 10 reviewed GT>C pairs, validate it, and run cache-only 10-pair / 20-step winner-anchor-only. The training loop must load cached tensors and E_ref_winner, not reference, loser, or VAE.

## Explicit Non-Runs

No standard DPO, strict SDPO, Linear-DPO, safe-linear DPO, large DPO, StageB, GRPO, full-data StageA, broad-LoRA, B/C rollout, checkpoint deletion, video generation, or video/weight push is authorized in v8d.
