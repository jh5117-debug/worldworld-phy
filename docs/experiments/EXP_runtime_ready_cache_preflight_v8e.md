Current Status:
GPU_BLOCKED_BEFORE_RUNTIME_READY_RUN

### GPU Policy Correction

The previous v8e GPU policy correction was itself wrong. Correct policy: use H20 physical GPU4-7 only for this task. Do not use H20 GPU0-3, and do not use PAI GPU0/1. If H20 GPU4-7 are occupied, v8e remains blocked rather than falling back to other GPUs.

# Actual Result 2026-07-02 10:28 CST

- PRD was committed and pushed before execution.
- Runtime-ready diagnostic code was implemented and pushed.
- GPU preflight was not run because physical GPU4-7 were occupied by existing Python jobs.
- GPU0-3 and PAI GPU0/1 are not authorized for this task and were not used.
- one-pair minimal_no_ref, with_ref, cache10, validation, and training were not run.
- Decision: `GPU_BLOCKED_BEFORE_RUNTIME_READY_RUN`.

Current Status:
PLANNED_RUNTIME_READY_CACHE_PREFLIGHT_V8E

# EXP Runtime-Ready Cache Preflight v8e

Updated: 2026-07-02 10:18 CST

This experiment follows docs/experiments/PRD_VISUAL_AUDIT_POLICY.md. It consumes already reviewed GT>C pairs from manifests/dpo_smoke_v7_gt_c_10.jsonl and does not create new DPO-ready pairs.

## Current Status

- v8b sigma diagnosis: PASS; sigma/timestep mapping is no longer the blocker.
- v8c 1-pair/window49 winner-anchor-only: PASS with positive post-update winner improvement.
- v8d cache-only code: connected, but cache build timed out before the first row.
- v8d progress: reached after_policy_load, did not reach after_runtime_ready.

## Problem

The 10-pair cache build and the 1-pair smoke did not reach after_runtime_ready; no cache row was written. It is unclear which component stalls: VAE, T5/text encoder, camera condition packer, LingBot runtime initialization, reference energy, video decode, latent write, or filesystem I/O.

## Hypothesis

Runtime-ready must be split into bounded stages with heartbeat output. Building the first cache row should be decomposed into video decode, window selection, VAE encode, prompt encode, camera condition pack, future-mask construction, tensor save, optional reference energy, and index write. We should first build a no-reference minimal cache row, then add E_ref_winner only after the minimal path passes.

## Inputs

- Pair manifest: manifests/dpo_smoke_v7_gt_c_10.jsonl
- Pair subset: first reviewed GT>C pair for preflight
- used_window_frames = 49
- prefix_len = 5
- prediction_start_frame = 5

## GPU Policy

- Use H20 physical GPU4-7 only for v8e.
- Do not use H20 physical GPU0-3.
- Do not use PAI GPU0/1 for this task.
- Prefer an actually free H20 GPU among 4-7; if all are occupied, do not launch.

## Method

1. Run runtime-ready debug with per-stage start/done/timeout rows and heartbeat.
2. Build one-pair minimal_no_ref cache.
3. Only if minimal passes, build one-pair with_ref_energy cache.
4. Only if with-ref passes, build bounded 10-pair cache.
5. Validate any successful 10-pair or partial cache subset.
6. Do not run training unless runtime-ready, one-pair minimal, one-pair with-ref, cache10, and validation all pass quickly and GPU remains free.

## Metrics

- Stage elapsed seconds
- Per-stage status and timeout reason
- CUDA allocated/reserved/max memory
- Cache row success/failure count
- Tensor shape/dtype/finite checks
- E_ref_winner_cached when applicable
- actual sigma/timestep when applicable
- sha256 verification

## Success Gate

- Runtime-ready stage report identifies the slow component.
- One-pair no-reference cache row is written.
- One-pair with-reference cache row is written.
- 10-pair cache writes all rows, or at minimum writes incremental rows with explicit success/failure status.
- No stage exceeds timeout silently.

## Failure Gate

- Any stage exceeds timeout without progress.
- First row still not written.
- Runtime init OOM.
- VAE/T5/camera packer cannot initialize.
- Cache invalid.

## Output Paths

- Reports: reports/dpo_objective_diagnosis_v8e/
- Cache assets: local_assets/dpo_objective_cache_v8e/

## What Is Explicitly Not Run

No DPO, SDPO, Linear-DPO, Safe-linear, DPO scale, pair factory rollout, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or video/weight push.

## Git Checkpoints

- Commit PRD before execution.
- Commit runtime-ready/cache diagnostic code before GPU run.
- Commit final reports/docs after v8e run or block.
