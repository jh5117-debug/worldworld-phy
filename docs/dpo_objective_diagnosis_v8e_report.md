Current Status:
GPU_BLOCKED_BEFORE_RUNTIME_READY_RUN

# DPO Objective Diagnosis v8e Report

Updated: 2026-07-02 10:28 CST

## Summary

v8e PRD was committed and pushed before execution. Runtime-ready diagnostic code was implemented and pushed. The planned GPU preflight did not run because all authorized GPUs (physical GPU4-7) remained occupied by existing `/usr/bin/python3` jobs using about 66 GB per GPU, with nonzero utilization. GPU0-3 were not authorized and were not used.

## v8d Readback

- v8d cache builder / validator / cache-only runner are connected.
- v8d blocker is between `after_policy_load` and `after_runtime_ready`.
- v8d wrote no first cache row.
- v8c 1-pair/window49 winner-anchor remains the latest positive objective sanity evidence.

## v8e Implementation

- Added runtime-ready stage debugger: `cam_physgeo/dpo/winner_anchor_runtime_ready_debug.py`.
- Added heartbeat/stage timeout logging for runtime-ready stages.
- Updated cache builder to accept `--cache_level minimal_no_ref` and `--cache_level with_ref_energy` plus heartbeat/timeout arguments.
- Added lightweight unit test for `StageLogger`.

## Runtime-Ready Debug

Status: `NOT_RUN_GPU4_7_OCCUPIED`

No runtime-ready GPU command was launched because GPU4-7 were not free. Therefore no stage-level runtime result exists yet.

## Cache Build

- one-pair minimal_no_ref: `NOT_RUN_GPU4_7_OCCUPIED`
- one-pair with_ref: `NOT_RUN_AFTER_MINIMAL_NOT_RUN`
- 10-pair cache: `NOT_RUN_AFTER_WITH_REF_NOT_RUN`

## Cache Validation

Status: `NOT_RUN_NO_CACHE_BUILT`

## Cache-Only Training

Status: `TRAINING_NOT_RUN_CACHE_PREFLIGHT_ONLY`

No winner-anchor optimizer step was run in v8e.

## Decision

Strict SDPO / Linear-DPO should not run next. DPO cannot proceed. The immediate next action is to rerun v8e runtime-ready preflight when GPU7 or GPU6 is actually free, starting with:

`CUDA_VISIBLE_DEVICES=7 python -m cam_physgeo.dpo.winner_anchor_runtime_ready_debug ...`

## Explicit Non-Runs

No DPO, SDPO, Linear-DPO, Safe-linear, large DPO, StageB, GRPO, full-data StageA, broad-LoRA, pair-factory rollout, checkpoint deletion, video generation, or video/weight push was performed.

## Runtime-Ready GPU7 Result 2026-07-02 17:47 CST

Current Status:
BLOCKED

GPU7 runtime-ready debug was launched after H20 GPU4-7 became available. The task did not run DPO or cache training. The run exposed missing Python dependencies first, then reached the real runtime blocker:

- video decode: PASS, about 29-32 seconds
- window selection: PASS
- policy runtime load: TIMEOUT_RUNNING after >180 seconds, heartbeats continued through about 266 seconds
- GPU7 memory during policy runtime: stayed near idle, no model allocation observed

Decision: `RUNTIME_READY_BLOCKED_6_LOAD_POLICY_RUNTIME_TIMEOUT`.

Next step: split `stage 6_load_policy_runtime` into sub-stages so we can identify whether the slow point is module import, checkpoint/config resolution, text runtime, DiT/Wan runtime, LoRA adapter load, or model-to-GPU transfer.
