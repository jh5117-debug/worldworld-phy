Current Status: PRD_READY_NOT_RUN

# EXP: Safe Wan Loader Runtime Patch v8h

Updated: 2026-07-03 06:07 CST

## Current Status

v8g direct safe `WanModelFast.from_pretrained` passed on CPU and GPU7. Integrated Stage1 helper/runtime wrapper still timed out at `14_construct_policy_model_cpu` around 309 sec before runtime_ready.

## Problem

The policy runtime/cache path still goes through a broad wrapper instead of the proven direct safe Wan policy-only path. It may use extra helper overhead, scans, T5/VAE hooks, or an indirect call that exceeds the bounded timeout.

## Hypothesis

A dedicated `safe_wan_policy_only` loader can bypass the broad helper path and load only the Fast policy with explicit local safetensors + low CPU memory args, no T5, no VAE, no reference, no loser, no DPO, no optimizer, and no distributed init.

## Goal

Implement `cam_physgeo.dpo.safe_wan_policy_loader.load_wan_policy_safe`, patch runtime/cache callers to support `--loader_mode safe_wan_policy_only`, retry policy runtime debug, and if it passes write one-pair minimal cache first row.

## Inputs

- `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- `reports/dpo_objective_diagnosis_v8g/*`
- Fast model root `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam`
- Fast subfolder `lingbot_world_fast`

## GPU Policy

Use H20 GPU4-7 only. Prefer physical GPU7 through `CUDA_VISIBLE_DEVICES=7` and process `--gpu 0`.

## Success Gate

- Runtime debug reaches `policy_runtime_ready` using `loader_mode=safe_wan_policy_only`.
- T5/VAE/reference/loser/DPO paths remain skipped.
- One-pair minimal cache writes first row if runtime passes.
- No OOM / SIGFPE / NaN.

## Failure Gate

- Safe loader is not actually called.
- Wrapper still times out after non-destructive caller patches.
- GPU0-3 would be required.
- Cache first row is blocked by a non-fixable runtime/schema issue.

## Output Paths

- `reports/dpo_objective_diagnosis_v8h/runtime_wrapper_callsite.md`
- `reports/dpo_objective_diagnosis_v8h/policy_runtime_load_debug_after_safe_loader.jsonl`
- `reports/dpo_objective_diagnosis_v8h/cache_build_one_pair_minimal_no_ref.csv`
- `reports/dpo_objective_diagnosis_v8h/self_review.md`
- `docs/dpo_objective_diagnosis_v8h_report.md`

## What Is Not Run

No DPO, SDPO, Linear-DPO, Safe-linear, large DPO, StageB, GRPO, full-data StageA, broad-LoRA, pair factory rollout, checkpoint deletion, video push, or weight push.

## Git Checkpoint

Commit and push this PRD/status before code execution with `Prepare safe Wan loader runtime patch v8h PRD`, then continue.
