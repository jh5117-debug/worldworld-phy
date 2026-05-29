# LingBot-Fast T5 Path Audit

## Summary

LingBot-Fast does not carry its own T5/text-tokenizer bundle in `local_assets/weights/lingbot_fast`. The active Fast smoke path uses a runtime bundle under `local_assets/cache/lingbot_fast_cam_runtime` that points Fast DiT shards to `lingbot_fast` and companion Wan assets to `lingbot_base`.

## Active Paths

- Fast root: `local_assets/weights/lingbot_fast`
- Base root: `local_assets/weights/lingbot_base`
- Runtime bundle: `local_assets/cache/lingbot_fast_cam_runtime`
- LingBot code: `local_assets/third_party/lingbot_world`
- LingBot env: `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2`

The env path is outside `local_assets` because it is a Python environment, not a model/data asset. Active data and model assets remain under `local_assets`.

## T5 And Tokenizer Candidates

Primary active candidates:

- T5 checkpoint: `local_assets/cache/lingbot_fast_cam_runtime/models_t5_umt5-xxl-enc-bf16.pth`
- Base fallback T5 checkpoint: `local_assets/weights/lingbot_base/models_t5_umt5-xxl-enc-bf16.pth`
- Tokenizer root: `local_assets/cache/lingbot_fast_cam_runtime/google/umt5-xxl`
- Base fallback tokenizer root: `local_assets/weights/lingbot_base/google/umt5-xxl`

Observed tokenizer files in the Base tokenizer root:

- `special_tokens_map.json`
- `tokenizer_config.json`
- `spiece.model`
- `tokenizer.json`

Observed Fast files:

- `config.json`
- `diffusion_pytorch_model.safetensors.index.json`
- 16 Fast shard files named `model-*-of-00016.safetensors`

## Answers

1. LingBot-Fast config does not appear to include the full T5/tokenizer bundle. The current runtime resolves T5/tokenizer from the Base companion assets through `local_assets/cache/lingbot_fast_cam_runtime`.
2. The active candidate T5 and tokenizer paths were observed in `local_assets`.
3. The active model/tokenizer paths are under `local_assets`; only the Python env path is outside.
4. Tokenizer files `tokenizer.json`, `spiece.model`, and `tokenizer_config.json` exist. A tokenizer-local `config.json` was not observed in the earlier file listing.
5. Multiple T5 candidates exist: runtime bundle symlink path and Base root path. The runtime bundle is the active one.
6. Previous runtime code did not force offline mode. The patched code supports `--local-files-only` and sets `TRANSFORMERS_OFFLINE=1`, `HF_HUB_OFFLINE=1`, and `HF_DATASETS_OFFLINE=1` for child runtime probes.
7. Offline/local-only mode is now explicit in `probe_lingbot_t5.py` and `run_inference.py`.
8. Active project cache root is `local_assets/cache`; exact HuggingFace runtime cache env variables still need confirmation from a successful H20 probe.
9. `WanI2VFast` smoke currently passes `t5_cpu=False`, so the real pipeline may place T5 on GPU. The independent probe supports both CPU and CUDA.
10. The exact `transformers` version is recorded by `probe_lingbot_t5.py` when it can run in the LingBot env.

## Current Blocker

Previous direct probes showed `torch` import and `wan` import succeed, then `WanI2VFast.__init__` times out. A narrower T5-only probe reached `T5EncoderModel(...)` and timed out, making Base T5/tokenizer/checkpoint initialization the first confirmed blocker.
