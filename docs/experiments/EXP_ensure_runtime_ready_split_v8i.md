Current Status:
DIAGNOSTIC_ONLY

# EXP Ensure Runtime Ready Split v8i

Updated: 2026-07-03T07:24:57

## Current Status

- v8h safe Wan policy loader PASS.
- policy runtime reaches `22_policy_runtime_ready`.
- first cache row blocked before `after_runtime_ready`.
- current blocker = `ensure_runtime_ready(backend)`.

## Problem

`ensure_runtime_ready` is too coarse. The cache builder reached `after_policy_load`, then did not reach `after_runtime_ready`. It is unclear whether the slow stage is VAE, T5/text, prompt encode, camera condition packer, prefix packer, VAE encode readiness, or backend component setup.

## Hypothesis

Backend readiness can be split into bounded stages. Policy-only minimal cache should not require unnecessary T5/VAE components unless the cache actually needs latent/text tensors. If VAE/T5 are required, they should load with heartbeat and explicit timeout. First cache row should be written once minimal components are ready.

## Inputs

- `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- v8h reports under `reports/dpo_objective_diagnosis_v8h/`
- safe Wan loader code from v8h

## GPU

- H20 physical GPU4-7 only.
- Prefer physical GPU7 via `CUDA_VISIBLE_DEVICES=7`, process `--gpu 0`.
- Do not use GPU0-3.

## Debug Plan

1. Instantiate backend with safe Wan policy loader.
2. Confirm policy runtime loaded.
3. Split `ensure_runtime_ready` into stages:
   - inspect helper components
   - runtime component decision
   - bootstrap imports if needed
   - VAE load/skip
   - T5 load/skip
   - move runtime components
   - prompt encode/stub decision
   - camera pack readiness
   - future mask / latent index mapping
4. Attempt one-pair minimal cache row only after bounded readiness succeeds.
5. If a substage blocks, patch/debug that substage before proceeding.

## Success Gate

- exact substage identified, or `after_runtime_ready` reached;
- one-pair minimal cache first row written if readiness allows;
- no silent 10-min wait;
- no DPO training.

## Failure Gate

- still black-box timeout;
- no heartbeat;
- safe loader not used;
- hidden T5/VAE load without stage logging;
- GPU0 used;
- destructive fix needed.

## Output Paths

- `reports/dpo_objective_diagnosis_v8i/backend_runtime_ready_debug.jsonl`
- `reports/dpo_objective_diagnosis_v8i/backend_runtime_ready_debug_summary.md`
- `reports/dpo_objective_diagnosis_v8i/cache_build_one_pair_minimal_no_ref.csv`
- `reports/dpo_objective_diagnosis_v8i/self_review.md`
- `docs/dpo_objective_diagnosis_v8i_report.md`

## What Is Not Run

- no DPO
- no SDPO
- no Linear-DPO
- no Safe-linear
- no cache10 training
- no pair factory rollout
- no StageB
- no GRPO
- no full-data StageA
- no broad-LoRA
- no checkpoint deletion
- no videos/weights pushed

## Git Checkpoint Before

Base HEAD before v8i PRD: `84db813`.

## Post-run Update

Pending.
