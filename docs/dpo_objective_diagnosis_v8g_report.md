Current Status: POLICY_SAFE_STANDALONE_PASS_STAGE1_HELPER_STILL_TIMEOUT

# DPO Objective Diagnosis v8g Report

## Scope

v8g split the `WanModelFast.from_pretrained(...)` bottleneck found in v8f. No DPO, SDPO, Linear-DPO, Safe-linear, StageB, GRPO, full-data StageA, broad-LoRA, rollout, or checkpoint deletion was run.

## Source Discovery

- WanModelFast class path: `/home/nvme03/workspace/lingbot-world/wan/modules/model_fast.py`
- from_pretrained source/wrapper: `/usr/local/lib/python3.10/dist-packages/huggingface_hub/utils/_validators.py`
- model root: `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam`
- Fast subfolder: `lingbot_world_fast`

## Checkpoint Inventory

- shard count: 16
- total shard size: 69.08 GB
- largest shard: 4.61 GB
- location: `/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast`
- all referenced shards checked by inventory: yes

## Shard Timing

- metadata timing: PASS, 16 shard rows, max metadata time 0.0098 sec
- first3 tensor timing: PASS, tensor load times [0.0416, 0.0391, 0.0411] sec
- conclusion: basic filesystem metadata and safetensors deserialization are not the blocker.

## Empty Model / State Dict Split

- empty/meta construction: CONSTRUCT_EMPTY_MODEL_PASS
- parameter count reported: 18,544,332,864
- state-dict prefix load: STATE_DICT_SHARD_LOAD_PREFIX_PASS for first 3 shards
- limitation: full state_dict injection into the live model was not completed in v8g; only shard prefix load and standalone from_pretrained were tested.

## Safe `from_pretrained` Result

- CPU-only safe args: POLICY_FROM_PRETRAINED_SAFE_CPU_PASS
- GPU move safe args: POLICY_FROM_PRETRAINED_SAFE_GPU_PASS
- CPU safe stage time in GPU run: 112.68 sec
- move-to-GPU time: 54.47 sec
- GPU allocated at move completion: 34.62 GB
- safe args: `local_files_only=True`, `use_safetensors=True`, `low_cpu_mem_usage=True`, `torch_dtype=bf16`

## Stage1 Helper Patch / Runtime Debug

The Stage1 Fast policy loader was patched to use the same safe args. After patch, the policy runtime debug still timed out at:

- blocked stage: `14_construct_policy_model_cpu`
- final status: `POLICY_RUNTIME_LOAD_BLOCKED_14_CONSTRUCT_POLICY_MODEL_CPU`
- stages completed before timeout: 0_initial, 1_import_basic_python, 2_import_torch, 3_import_diffusers_transformers_peft, 4_import_lingbot_modules, 5_resolve_repo_paths, 6_resolve_config_path, 7_read_config, 8_resolve_model_weight_paths, 9_check_weight_file_sizes, 10_load_tokenizer_or_text_runtime_cpu, 11_load_t5_or_text_encoder_cpu, 12_load_vae_cpu, 13_load_policy_config_cpu
- last timeout elapsed: 309.81 sec
- last CPU RSS before timeout: 2.88 GB
- GPU allocated during blocked Stage1 helper load: 0.0 GB

Interpretation: direct `WanModelFast.from_pretrained` with safe args can load and move to GPU, but the current Stage1 helper/runtime debug path still exceeds the 300 sec stage boundary before LoRA/move-to-GPU/runtime_ready. It is no longer a raw shard metadata/tensor IO blocker; the remaining blocker is the integrated Stage1 helper construction path or wrapper overhead around `from_pretrained`.

## Cache First Row

- one-pair cache first row: NOT_ATTEMPTED
- reason: policy runtime after-patch did not reach runtime_ready within the bounded stage timeout.

## Pair Factory Bookkeeping

See `reports/scale_gt_c_pair_factory_v8/condition_recovery_bookkeeping_v8g.csv` and `.md`. This was read-only; no rollout or video generation was run.

## Decision

- DPO cannot proceed yet.
- Strict SDPO / Linear-DPO should not run next.
- Exact next step: split the Stage1 helper policy construction path further or make the winner-anchor/cache path call the proven direct safe loader instead of the broader Stage1 helper runtime.
