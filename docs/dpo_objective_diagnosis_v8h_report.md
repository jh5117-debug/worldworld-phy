Current Status:
MIXED

# DPO Objective Diagnosis v8h Report

Updated: 2026-07-03T06:46:04

## Goal

Patch the v8f/v8g policy runtime path so that the integrated loader uses the known-good safe Wan loading route, then attempt a bounded one-pair cache first row.

## Code changes

- Added `cam_physgeo/dpo/safe_wan_policy_loader.py`.
- Added safe loader smoke coverage in `tests/test_safe_wan_policy_loader.py`.
- Updated `cam_physgeo/dpo/policy_runtime_load_debug.py` with `--loader_mode safe_wan_policy_only`, `--skip_text`, and `--skip_vae`.
- Updated `cam_physgeo/dpo/lingbot_fast_energy.py` so the DPO energy backend can use the safe Wan policy loader and keep LoRA loading separate.
- Updated `cam_physgeo/dpo/winner_anchor_cache_builder.py` with `--loader_mode` so cache precompute can request the safe loader path.

## Policy runtime result

Command output: `reports/dpo_objective_diagnosis_v8h/policy_runtime_load_debug_after_safe_loader.jsonl`.

Summary:

- `safe_from_pretrained_cpu`: PASS, about 83.5 sec.
- `16_load_lora_adapter_cpu_if_needed`: PASS.
- `19_move_policy_to_gpu`: PASS, about 73.4 sec.
- `22_policy_runtime_ready`: PASS.
- Peak GPU allocation: about 34.64 GiB on physical GPU7.
- No GPU0-3 used by this v8h run.
- Final status: `POLICY_RUNTIME_LOAD_PASS`.

This resolves the previous broad-loader timeout for the policy-only runtime debug path.

## First-row cache smoke

Command output:

- progress: `reports/dpo_objective_diagnosis_v8h/cache_build_one_pair_minimal_no_ref_progress.jsonl`
- safe loader progress: `reports/dpo_objective_diagnosis_v8h/cache_build_one_pair_minimal_no_ref_progress_safe_loader.jsonl`
- termination record: `reports/dpo_objective_diagnosis_v8h/cache_first_row_termination_record.txt`

Observed progress:

- `start`: PASS
- `before_backend_load`: PASS
- safe policy load: PASS
- `after_policy_load`: PASS
- `after_runtime_ready`: NOT REACHED
- `pair_start`: NOT REACHED
- cache CSV rows: 0
- cache tensor files: 0

The process ran about 10 minutes and was terminated with TERM after no heartbeat past `after_policy_load`.

Decision: `CACHE_FIRST_ROW_BLOCKED_AT_ENSURE_RUNTIME_READY`.

## Scientific / engineering decision

DPO cannot proceed yet. Strict SDPO / Linear-DPO / Safe-linear should not run until the reusable cache path can reach at least one validated first row and then cache10. The next technical blocker is not sigma mapping or policy model loading; it is runtime component readiness after policy load.

## Next step

Create the next diagnosis to split `ensure_runtime_ready(backend)` into stages:

- VAE runtime load
- T5/text runtime load, or explicit skip if not needed
- prompt embedding path
- camera condition packer
- VAE encode readiness
- any hidden full runtime setup called by `ensure_runtime_ready`

Only after first-row cache PASS should cache10 / winner-anchor 10-pair training be attempted.

## Explicit non-runs

- no DPO
- no SDPO
- no Linear-DPO
- no Safe-linear
- no large DPO
- no StageB
- no GRPO
- no full-data StageA
- no broad-LoRA
- no checkpoint deletion
- no videos/weights pushed
