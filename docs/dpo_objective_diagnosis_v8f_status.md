Current Status:
PRD_READY_NOT_RUN

# DPO Objective Diagnosis v8f Status

Updated: 2026-07-02 18:55 CST

## Readback

v8e ran on H20 physical GPU7. Stages 0-5 passed: initial, manifest parse, pair selection, path resolution, CPU winner decode, and window index selection. v8e blocked at `6_load_policy_runtime` after heartbeats to about 266 seconds. GPU memory stayed nearly idle, so the stall likely happened before model weights reached CUDA.

## Corrected GPU Policy

Use H20 physical GPU4-7 only. Prefer GPU7; use GPU6 only if GPU7 is not available. Do not use H20 GPU0-3. Do not use PAI GPU0/1.

## Current Blocker

`load_policy_runtime` is too coarse and may hide imports, config discovery, checkpoint resolution, tokenizer/T5, VAE, DiT/LingBot construction, shard loading, LoRA loading, dtype conversion, move-to-GPU, SDPA/xformers setup, accidental distributed init, or slow filesystem scan.

## v8f Objective

Split policy runtime loading into bounded substages with heartbeat output and identify the exact blocked substage. This round does not run DPO, SDPO, Linear-DPO, Safe-linear, cache10 training, pair factory rollout, StageB, GRPO, full-data StageA, or broad-LoRA.
