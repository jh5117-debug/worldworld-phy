Current Status:
POLICY_RUNTIME_LOAD_BLOCKED_14_CONSTRUCT_POLICY_MODEL_CPU

## 2026-07-02 v8f Result

The policy-only v8f run on H20 physical GPU7 matched v8e's skip-runtime path and blocked at `14_construct_policy_model_cpu` / `WanModelFast.from_pretrained`. Imports, config, weight path resolution, and policy config all passed. Tokenizer/T5/VAE were also tested separately: T5 CPU load timed out after ~185s, but that is a secondary runtime bottleneck rather than the exact v8e policy-only blocker. No DPO or cache row ran.

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

## Verification

- `python -m compileall cam_physgeo src tests`: PASS.
- `pytest`: BLOCKED_BY_ENV because `/usr/bin/python3` has no `pytest` module.
- Direct smoke for `StageLogger` and `run_stage`: PASS (`reports/dpo_objective_diagnosis_v8f/test_logs/direct_smoke_policy_runtime_load_debug.jsonl`).

## Explicit Non-Runs

No DPO, SDPO, Linear-DPO, Safe-linear, large DPO, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, video push, image push, or weight push occurred.
