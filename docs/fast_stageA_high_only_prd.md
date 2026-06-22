# Fast StageA High-Only PRD

Status: active_correction

## Purpose

This PRD replaces the invalid Base low-to-high StageA interpretation. The corrected StageA is a LingBot-World-Fast high-noise-only warmup for global structure, camera-conditioned geometry, background stability, and coarse world persistence.

## Non-Goals

This task does not run:

- StageB
- DPO
- reward scoring
- rollout
- pair mining
- LingBot-Base training
- full model finetuning

## Required Model

Policy weights must come from:

`/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast`

Shared assets such as VAE, T5, tokenizer, and shared config may come from:

`/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam`

Base policy folders such as `low_noise_model` and `high_noise_model` must not be used as the Fast StageA policy.

## Required Training Policy

- `model_family: lingbot_world_fast`
- `stage_name: stageA`
- `branch_mode: high_only`
- `noise_policy: high_only`
- `high_noise_probability: 1.0`
- `low_noise_probability: 0.0`
- `control_type: cam`
- `use_action: false`

## Stage Boundary

StageA: high-noise/global-camera warmup.

StageB: future low/mixed-noise detail refinement. StageB is not part of this run.

## Data

The formal run must use a new generated_v5 Stage1-ready immutable snapshot built from completed, converted chunks only. The active TDW chunk must be excluded.

## Gates

Formal training may start only after:

1. Fast loader smoke passes.
2. BF16 diagnostics pass for basic kernels and Fast preflights.
3. Single-GPU, 2-GPU, and 7-GPU high-only preflights pass.
4. Fixed validation is checkpoint-invariant.
5. GPU0 guard passes.
6. generated_v5 snapshot is richer than the old drop-heavy snapshot.

## Output

Output naming must use Fast high-only names such as:

- `fast_stageA_high_noise_adapter`
- `fast_stageA_high_noise_best`
- `fast_stageA_high_noise_last`

Forbidden output names for the corrected Fast StageA include:

- `low_phase`
- `low_noise_model`
- `complete_low_high_stageA_bundle`

## 2026-06-22 PRD Status

Current status: `preflight_pass_waiting_for_balanced_generated_v5_snapshot`.

The corrected Fast StageA path has now passed:

- 20-step single-GPU Fast high-only preflight on physical GPU7.
- 4-step two-GPU DDP Fast high-only preflight on physical GPU6/7 with fixed validation.
- 2-step seven-GPU DDP Fast high-only preflight on physical GPU1-7 with fixed validation.

The valid StageA noise policy is still high-only. StageB remains a later low/mixed-noise refinement phase and was not run. DPO, reward scoring, rollout and pair mining were not run.

Formal StageA must wait for a richer immutable generated_v5 snapshot. As of this update, converted Stage1-ready generated_v5 samples were still only `drop + orbit_left_72`, so a formal run would be unbalanced.
