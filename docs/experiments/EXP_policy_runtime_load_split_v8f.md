Current Status:
PRD_READY_NOT_RUN

# EXP: Policy Runtime Load Split Diagnosis v8f

Updated: 2026-07-02 18:55 CST

## Current Status

v7 DPO smoke was engineering-pass but signal-fail. v8b proved sigma/timestep mapping passes. v8c proved 1-pair/window49 winner-anchor can be memory-safe. v8d connected reusable cache code but timed out before the first cache row. v8e split runtime-ready preflight and showed stages 0-5 pass, then blocked at `6_load_policy_runtime`.

## GPU Policy

Run only on H20 physical GPU4-7. Prefer GPU7; fallback GPU6. Do not use H20 GPU0-3 or PAI GPU0/1.

## Problem

`load_policy_runtime` is too coarse. It timed out before runtime-ready while GPU memory was nearly idle, suggesting the stall is likely CPU/runtime/config/checkpoint/import related. Possible slow points include Python imports, config discovery, checkpoint resolution, tokenizer/T5 runtime, VAE runtime, LingBot/Wan model construction, shard loading, LoRA loading, dtype conversion, move-to-GPU, SDPA/xformers setup, distributed init, or slow filesystem scanning.

## Hypothesis

Fine-grained substages with heartbeat and per-stage timeout will expose the exact slow component or prove policy runtime can load successfully.

## Required Substages

`0_initial`, `1_import_basic_python`, `2_import_torch`, `3_import_diffusers_transformers_peft`, `4_import_lingbot_modules`, `5_resolve_repo_paths`, `6_resolve_config_path`, `7_read_config`, `8_resolve_model_weight_paths`, `9_check_weight_file_sizes`, `10_load_tokenizer_or_text_runtime_cpu`, `11_load_t5_or_text_encoder_cpu`, `12_load_vae_cpu`, `13_load_policy_config_cpu`, `14_construct_policy_model_cpu`, `15_load_policy_weights_cpu`, `16_load_lora_adapter_cpu_if_needed`, `17_enable_gradient_checkpointing_if_available`, `18_configure_sdpa_or_xformers`, `19_move_policy_to_gpu`, `20_cast_policy_dtype`, `21_freeze_base_set_lora_trainable`, `22_policy_runtime_ready`, `23_empty_cache_final`.

## Success Gate

Identify the exact blocked substage or reach `22_policy_runtime_ready`; write heartbeat for long stages; use only H20 GPU4-7; run no training.

## Failure Gate

Black-box timeout remains, heartbeat missing, wrong repo, H20 GPU0-3 used, local hal execution, or any DPO/cache10/pair-rollout training starts silently.

## Outputs

- `reports/dpo_objective_diagnosis_v8f/policy_runtime_load_debug.jsonl`
- `reports/dpo_objective_diagnosis_v8f/policy_runtime_load_debug_summary.md`
- `reports/dpo_objective_diagnosis_v8f/blackbox_loader_split.md`
- `docs/dpo_objective_diagnosis_v8f_report.md`

## What Is Not Run

No DPO, SDPO, Linear-DPO, Safe-linear, cache10 training, pair factory rollout, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or video/weight push.
