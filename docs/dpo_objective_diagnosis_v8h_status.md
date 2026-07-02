Current Status:
MIXED

# DPO Objective Diagnosis v8h Status

Updated: 2026-07-03T06:46:04

## What v8h tested

v8h patched the policy runtime path to use a safe Wan loader instead of the earlier broad helper path that timed out around `WanModelFast.from_pretrained(...)`.

The patched path uses:

- `local_files_only=True`
- `use_safetensors=True`
- `low_cpu_mem_usage=True`
- explicit LingBot base path and `lingbot_world_fast` subfolder
- no loser branch
- no reference branch
- no DPO / SDPO / Linear-DPO objective
- physical GPU7 only via `CUDA_VISIBLE_DEVICES=7` and process `--gpu 0`

## Result

Policy runtime load now passes:

- stages 0-13: PASS
- text/T5 runtime: SKIPPED for policy-only debug
- VAE runtime: SKIPPED for policy-only debug
- `safe_from_pretrained_cpu`: PASS in about 83.5 sec
- LoRA adapter load: PASS
- move policy to GPU7: PASS in about 73.4 sec
- peak policy GPU allocation: about 34.64 GiB
- trainable LoRA params: 6,553,600
- total params: 18,550,886,464
- final status: `POLICY_RUNTIME_LOAD_PASS`

## Cache first-row smoke

A one-pair `minimal_no_ref` cache first-row smoke was launched after policy runtime PASS.

Observed progress:

- `start`: written
- `before_backend_load`: written
- `after_policy_load`: written
- `after_runtime_ready`: NOT written
- `pair_start`: NOT written
- cache CSV rows: 0
- cache tensor files: 0

The process ran for about 10 minutes without further heartbeat after `after_policy_load`, with GPU7 around 36 GiB. It was terminated cleanly with TERM to release GPU7.

Decision:

`POLICY_RUNTIME_LOAD_PASS_CACHE_FIRST_ROW_BLOCKED_AT_ENSURE_RUNTIME_READY`

## Interpretation

v8h fixes the previous policy loader bottleneck. The remaining blocker is now inside `ensure_runtime_ready(backend)` / runtime component preparation before first pair cache construction. This likely involves VAE/T5/runtime component initialization or hidden condition-packer setup. It is not the earlier `WanModelFast.from_pretrained` blocker.

## What was not run

- no DPO
- no SDPO
- no Linear-DPO
- no Safe-linear
- no large DPO
- no StageB
- no GRPO
- no full-data StageA
- no broad-LoRA
- no pair factory rollout
- no checkpoint deletion
- no videos or weights pushed
