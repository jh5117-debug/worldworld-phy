# V2V-5 Generation Wrapper Report

Updated: 2026-06-27

## Status

Implemented and unit-tested. The wrapper is designed to fail fast unless `prefix_len=5` and `prediction_start_frame=5`.

## What Changed

- Added `cam_physgeo/eval/prefix_video_condition.py` for prefix frame loading, future zeroing, Wan latent visible mask construction, future extraction, and contact-sheet helpers.
- Added `cam_physgeo/eval/v2v5_generation_wrapper.py`, which mirrors the LingBot-Fast denoising loop but replaces the native image-only condition with a prefix-video condition.
- Added `cam_physgeo/eval/run_v2v5_inference.py` CLI for Original Fast / adapter V2V-5 rollout.
- Added tests proving that prefix frames 0-4 enter the VAE condition and frames 5-80 are zeroed.

## Proof Against Image-Only Fallback

The native `WanI2VFast.generate(prompt, image, action_path=...)` path only encodes frame 0. The new wrapper calls `prepare_prefix_condition_latent`, which builds a full 81-frame condition video with frames 0-4 copied from the prefix and frames 5-80 zeroed. The Wan mask marks latent slots touched by raw prefix frames as visible.

## Tests

- `python -m pytest -q tests/test_prefix_video_condition.py tests/test_v2v5_generation_wrapper.py`
- Result: 5 passed.

## Next Step

Run Original Fast V2V-5 baseline rollout on `manifests/screen16_v2v5.jsonl`, then use the same wrapper for short StageA checkpoint evaluation.
