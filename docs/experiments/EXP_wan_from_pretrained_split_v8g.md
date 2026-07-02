Current Status:
PRD_READY_NOT_RUN

# EXP: WanModelFast from_pretrained Split Diagnosis v8g

Updated: 2026-07-02 21:30 CST

## Current Status

v7 DPO smoke is engineering-pass but objective-signal-fail. v8b sigma/timestep mapping passed. v8c proved 1-pair/window49 winner-anchor can complete with positive post-update winner improvement. v8d cache build blocked before first row. v8e blocked at coarse `load_policy_runtime`. v8f split that stage and identified the exact policy-only blocker as `WanModelFast.from_pretrained(...)` during CPU-side policy construction / checkpoint shard loading.

## Problem

`WanModelFast.from_pretrained(...)` is a black-box bottleneck. It times out before LoRA loading or move-to-GPU. The slow substage may be config resolution, model class construction, shard index parsing, safetensors load, state_dict injection, CPU RAM pressure, filesystem behavior, or diffusers loader behavior.

## Hypothesis

The blocker can be localized by separating source discovery, config read, model directory and index resolution, shard listing, safetensors metadata load, bounded tensor load, empty model construction, state_dict loading, LoRA loading, dtype cast, and move-to-GPU.

## Goal

Produce per-stage and per-shard timing. Identify the exact slow or blocked substage. Avoid another 6-minute black-box wait. Write progress every 15 seconds for long operations. Do not train.

## Success Gate

- Exact `from_pretrained` substage identified, or policy model loads successfully.
- No silent timeout.
- No H20 GPU0-3 usage.
- No data, checkpoint, or weight deletion.

## Failure Gate

- Still black-box timeout.
- Cannot locate source.
- Checkpoint index missing.
- Shard load impossible.
- Filesystem read stalls without progress.

## Outputs

- `reports/dpo_objective_diagnosis_v8g/wan_source_discovery.json`
- `reports/dpo_objective_diagnosis_v8g/checkpoint_inventory.csv`
- `reports/dpo_objective_diagnosis_v8g/shard_metadata_timing.csv`
- `reports/dpo_objective_diagnosis_v8g/shard_tensor_timing_first3.csv`
- `reports/dpo_objective_diagnosis_v8g/construct_empty_model.jsonl`
- `reports/dpo_objective_diagnosis_v8g/state_dict_load_split.jsonl`
- `reports/dpo_objective_diagnosis_v8g/real_from_pretrained_safe.jsonl` only if prior stages pass
- `docs/dpo_objective_diagnosis_v8g_report.md`

## What Is Explicitly Not Run

No DPO, SDPO, Linear-DPO, Safe-linear, large DPO, cache10 training, pair factory rollout, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or video/weight push.

## Git Checkpoint

Commit and push this PRD/status before execution with `Prepare Wan from_pretrained split diagnosis v8g PRD`.
