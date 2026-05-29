# T5 Blocker Fix Recommendation

## Diagnosis

The blocker is not tokenizer load, checkpoint read, `torch.load`, or `load_state_dict`.

Main CPU bottleneck:

- UMT5-XXL architecture construction/random initialization and dtype/device setup.
- CPU fp32 construction takes about `264s`.

Secondary CPU bottleneck:

- CPU prompt encode takes about `109s`.

GPU bf16 path:

- Full T5 load and prompt encode succeeds in about `59s`.

## Minimal Fixes

1. For actual Fast smoke, use GPU bf16 T5 rather than CPU fp32.
2. Raise runtime timeout from `120s` to at least `600s`.
3. Keep unbuffered markers in `run_inference.py`.
4. Use `torch.load(..., mmap=True)` if LingBot T5 loader is patched, because it reduces initial checkpoint load latency and RSS.

## Longer-Term Fixes

- Avoid random initialization before loading checkpoint by using meta-device construction plus assign-style state loading, if compatible with this custom T5.
- Add a LingBot T5 loader option for `mmap=True`.
- Add a fixed-prompt cached embedding path only after it is wired into `WanI2VFast` without constructing T5.

## What Not To Do Yet

- Do not convert to safetensors without confirmation.
- Do not run rollout/reward/VideoGPA/DPO yet.
- Do not treat the old 120s timeout as a model failure.

## Next Minimal Action

Run one official LingBot-Fast minimal inference or one `cam_physgeo` actual inference with GPU 6/7, bf16 T5, unbuffered logging, and timeout at least `600s`. If it fails, the next blocker is likely VAE/Fast DiT/pipeline generation, not T5 tokenizer/checkpoint loading.
