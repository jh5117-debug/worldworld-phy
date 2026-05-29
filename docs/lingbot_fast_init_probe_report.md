# LingBot-Fast Initialization Probe Report

## Scope

This probe did not train, delete, move, or push any data or weights. It only ran short diagnostic imports and initialization probes in the LingBot environment using GPU visibility restricted to `CUDA_VISIBLE_DEVICES=6,7`.

## Environment

- Worktree: `world_model_phys_min_adapter_work`
- Runtime env: `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2`
- Runtime bundle: `local_assets/cache/lingbot_fast_cam_runtime`
- Bundle contents checked: Base T5 checkpoint, Base tokenizer, Base VAE, and `lingbot_world_fast` shards.

## Results

Direct unbuffered env Python probes showed:

- `torch` imports successfully and reports CUDA available.
- `wan` imports successfully.
- `WanI2VFast.__init__` starts after imports but does not complete within the smoke timeout.
- A narrower T5-only probe reaches `T5EncoderModel(...)` using `models_t5_umt5-xxl-enc-bf16.pth` and `google/umt5-xxl`, then times out before returning.

## Interpretation

The first confirmed LingBot-Fast blocker is Base T5/tokenizer/checkpoint initialization inside the Fast runtime bundle. The current failure is not caused by missing `poses.npy`, missing `intrinsics.npy`, or accidental use of `action.npy` as a model condition.

## Code Change

`cam_physgeo/eval/run_inference.py` now:

- uses direct `LINGBOT_ENV/bin/python -u` when available, instead of `conda run`, so smoke logs stream before timeout;
- preserves `PYTHONUNBUFFERED=1` in the child process;
- writes flushed runtime markers around import, image load, pipeline init, generation, and save;
- records the Python launcher, timeout, and log tail in `inference_metadata.json`.

## Next Diagnostic Step

Run the 1-sample smoke again with the patched logger. If the last marker is `pipeline_init_start`, investigate LingBot `wan/modules/t5.py` and the Fast `WanI2VFast` constructor for CPU-side T5 loading latency, tokenizer cache behavior, or a smoke-only cached text embedding path.
