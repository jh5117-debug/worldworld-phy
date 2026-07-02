Current Status Update (2026-07-02 21:58:17): V8G_FOLLOWUP_SAFE_LOADER_RESULT

v8g localized the v8f blocker further. Direct safe WanModelFast.from_pretrained can load CPU and move to GPU7, but the integrated Stage1 helper policy runtime still times out at 14_construct_policy_model_cpu before runtime_ready. No DPO-family training was run; DPO remains blocked until the helper/cache path uses the proven direct safe loader or is split further.

Current Status:
POLICY_RUNTIME_LOAD_BLOCKED_14_CONSTRUCT_POLICY_MODEL_CPU

# DPO Objective Diagnosis v8f Report

Updated: 2026-07-02 19:23 CST

## Summary

v8f split the v8e `load_policy_runtime` black box into bounded substages with heartbeat output. The run used H20 physical GPU7 only via `CUDA_VISIBLE_DEVICES=7` and process-local `--gpu 0`. No H20 GPU0-3, PAI GPU, DPO, SDPO, Linear-DPO, Safe-linear, StageB, GRPO, full-data StageA, or broad-LoRA was used.

## Two Debug Paths

### Full text/runtime path

The first v8f run loaded tokenizer/T5/VAE stages explicitly. It passed imports, config, checkpoint path resolution, weight-size checks, and tokenizer loading. It then timed out at `11_load_t5_or_text_encoder_cpu` after about 185 seconds. CPU RSS climbed to roughly 20.3 GB and GPU allocation stayed at 0 GB. This proves the T5/text runtime is itself too slow for the bounded preflight, but this path is not the exact v8e policy-only path.

### Policy-only path mirroring v8e

The second v8f run used `--skip_text_vae`, matching v8e's `dpo_skip_runtime_components_on_load=True` behavior. It passed or skipped:

- `0_initial` PASS
- `1_import_basic_python` PASS
- `2_import_torch` PASS
- `3_import_diffusers_transformers_peft` PASS
- `4_import_lingbot_modules` PASS
- `5_resolve_repo_paths` PASS
- `6_resolve_config_path` PASS
- `7_read_config` PASS
- `8_resolve_model_weight_paths` PASS
- `9_check_weight_file_sizes` PASS
- `10_load_tokenizer_or_text_runtime_cpu` SKIPPED/PASS for policy-only
- `11_load_t5_or_text_encoder_cpu` SKIPPED/PASS for policy-only
- `12_load_vae_cpu` SKIPPED/PASS for policy-only
- `13_load_policy_config_cpu` PASS

It then blocked at `14_construct_policy_model_cpu`, specifically the `WanModelFast.from_pretrained(...)` call. The stage ran for about 186 seconds, CPU RSS climbed to roughly 20.7 GB, and GPU allocation remained 0 GB. This means the original v8e blocker is CPU-side policy model construction / checkpoint shard loading before move-to-GPU.

## Weight Inventory

The bounded size scan found 20 relevant files totaling about 82,060.9 MB, including:

- VAE: about 484.1 MB
- T5: about 10,835.6 MB
- LingBot-Fast policy: 16 safetensor shards, each roughly 4.3-4.7 GB

## Exact Blocker

`POLICY_RUNTIME_LOAD_BLOCKED_14_CONSTRUCT_POLICY_MODEL_CPU`

The black-box call is `WanModelFast.from_pretrained`, inherited through diffusers/HuggingFace model loading. It combines model construction and checkpoint/shard loading. The current script identifies the exact outer call. The next diagnostic should instrument inside the diffusers/LingBot shard loading path or build a bounded local loader that logs per-shard progress.

## Cache First Row

Not attempted. The success gate required policy runtime load to pass first, and it did not pass.

## DPO Decision

DPO cannot proceed. Do not run SDPO, Linear-DPO, Safe-linear, or large DPO until policy runtime load and cache10 winner-anchor path are stable.

## Outputs

- `reports/dpo_objective_diagnosis_v8f/policy_runtime_load_debug.jsonl`
- `reports/dpo_objective_diagnosis_v8f/policy_runtime_load_debug_policy_only.jsonl`
- `reports/dpo_objective_diagnosis_v8f/policy_runtime_load_debug_summary.md`
- `reports/dpo_objective_diagnosis_v8f/blackbox_loader_split.md`
- `reports/scale_gt_c_pair_factory_v8/condition_recovery_bookkeeping_v8f.csv`
- `reports/scale_gt_c_pair_factory_v8/condition_recovery_bookkeeping_v8f.md`

## Verification

- `python -m compileall cam_physgeo src tests`: PASS.
- `pytest`: BLOCKED_BY_ENV because `/usr/bin/python3` has no `pytest` module.
- Direct smoke for `StageLogger` and `run_stage`: PASS (`reports/dpo_objective_diagnosis_v8f/test_logs/direct_smoke_policy_runtime_load_debug.jsonl`).

## Explicit Non-Runs

No DPO, SDPO, Linear-DPO, Safe-linear, large DPO, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, video push, image push, or weight push occurred.
