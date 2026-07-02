Current Status:
SUPERSEDED_BY_V8F_POLICY_LOAD_SPLIT

## 2026-07-02 v8f Follow-Up

v8d cache build timed out before first row because policy runtime initialization is blocked. v8f narrowed this to CPU-side `WanModelFast.from_pretrained` model construction / shard loading.

Current Status:
SUPERSEDED_BY_V8E_GPU_BLOCKED

## 2026-07-02 v8e Follow-Up

v8e added runtime-ready stage diagnostics but could not run GPU preflight because authorized GPUs 4-7 were occupied. v8d blocker remains active.

Current Status:
BLOCKED_CACHE_BUILD_RUNTIME_READY_TIMEOUT

# DPO Objective Diagnosis v8d Report

Updated: 2026-07-02 09:45 CST

## Summary

v8d implemented a reusable winner-anchor cache builder, cache validator, and cache-only training mode. The PRD was committed and pushed before execution. The source implementation was also committed and pushed before the run. The run then tested cache construction on physical GPU7.

The 10-pair cache build did not produce a first row after more than 6 minutes. A 1-pair cache smoke with progress logging showed the exact blocker: the process reached `after_policy_load` but did not reach `after_runtime_ready`. No pair-level decode, winner cache, reference-energy scalar, or cache tensor was written.

## Cache Build

- 10-pair build: started, stopped after no first row.
- 1-pair smoke: reached `after_policy_load`, blocked before `after_runtime_ready`.
- Cache rows: 0.
- Cache build status: `CACHE_BUILD_RUNTIME_READY_TIMEOUT`.
- Progress file: `reports/dpo_objective_diagnosis_v8d/cache_build_smoke_progress.jsonl`.

## Cache Validation

Cache validation was not run because cache build did not produce a complete cache index.

Status: `CACHE_VALIDATION_NOT_RUN_CACHE_BUILD_FAILED`.

## Cache-Only Winner Anchor

The 10-pair / 20-step cache-only winner-anchor run was not started. No optimizer step was run in v8d.

Status: `WINNER_ANCHOR_CACHE10_NOT_RUN_CACHE_BUILD_FAILED`.

## Training-Loop Isolation Status

- Reference in training loop: intended no, implemented in cache-only runner, but not exercised because cache build failed.
- Loser in training loop: intended no, implemented in cache-only runner, but not exercised because cache build failed.
- VAE in training loop: intended no, implemented by cache-only mode, but not exercised because cache build failed.

## Decision

DPO cannot proceed. Strict SDPO / Linear-DPO should not run next. The next blocker is earlier than 10-pair optimizer behavior: reusable cache construction must be made practical by fixing runtime component readiness, likely by reusing already initialized runtime components, splitting VAE/T5 initialization into a bounded preflight, or loading cache-builder runtime in a separate lighter process with incremental row writes before pair cache.

## Explicit Non-Runs

No standard DPO, strict SDPO, Linear-DPO, safe-linear DPO, large DPO, StageB, GRPO, full-data StageA, broad-LoRA, B/C rollout, checkpoint deletion, video generation, or video/weight push was performed.
