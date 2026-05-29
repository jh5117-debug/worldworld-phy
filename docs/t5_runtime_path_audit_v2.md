# T5 Runtime Path Audit V2

## Execution Worktree

- Requested project root checked: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys`.
- The requested root is a dirty worktree on branch `physion-only-local-assets-videogpa-smoke`.
- Debug execution used the clean auxiliary worktree: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_min_adapter_work`.
- Its `local_assets` is a symlink to the same project-local assets under the requested root.
- No data, weights, or checkpoints were moved or deleted.

## Runtime Paths

- T5 checkpoint path: `local_assets/cache/lingbot_fast_cam_runtime/models_t5_umt5-xxl-enc-bf16.pth`.
- T5 checkpoint realpath: `local_assets/weights/lingbot_base/models_t5_umt5-xxl-enc-bf16.pth`.
- T5 checkpoint size: `11361920418` bytes, `10.582 GiB`.
- T5 checkpoint is a symlink in the runtime bundle.
- Tokenizer path: `local_assets/cache/lingbot_fast_cam_runtime/google/umt5-xxl`.
- Tokenizer files present: `spiece.model`, `tokenizer.json`, `tokenizer_config.json`.
- Tokenizer-local `config.json`: not present.
- LingBot code path: `local_assets/third_party/lingbot_world`.
- Actual T5 module path: `local_assets/third_party/lingbot_world/wan/modules/t5.py`.
- LingBot env Python: `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python`.

## Version Audit

Observed during probes:

- `torch==2.11.0+cu128`
- `transformers==4.51.3`
- CUDA visible from the LingBot env.

The probe records `safetensors`, `sentencepiece`, `HF_HOME`, `TRANSFORMERS_CACHE`, `TRANSFORMERS_OFFLINE`, `HF_HUB_OFFLINE`, and `PYTHONPATH` in its JSON environment section. Offline probes were run with `TRANSFORMERS_OFFLINE=1` and `HF_HUB_OFFLINE=1`; tokenizer used local files.

## Runtime Bundle

`local_assets/cache/lingbot_fast_cam_runtime` points Fast inference at:

- Base T5 checkpoint;
- Base tokenizer;
- Base VAE;
- Fast DiT shards under `lingbot_world_fast`.

There are two practical T5 candidates: the runtime symlink path and the Base realpath. They point to the same 10.582 GiB checkpoint.
