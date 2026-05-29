# LingBot-Fast Cached Text Smoke Report

## Status

Cached text embedding bypass is not enabled.

`probe_lingbot_t5.py` can save a prompt embedding with:

```bash
python -m cam_physgeo.eval.probe_lingbot_t5 \
  --fast_root local_assets/weights/lingbot_fast \
  --prompt "A synthetic physical scene." \
  --save_embedding local_assets/cache/text_embeddings/synthetic_physical_scene.pt
```

However, `WanI2VFast` currently constructs its T5 encoder inside `WanI2VFast.__init__`. Passing a cached embedding to `cam_physgeo.eval.run_inference` would not skip that constructor path without modifying LingBot runtime internals.

## Implemented Guard

`run_inference.py` accepts:

- `--text-embedding-cache`
- `--skip-t5-if-cached`

but refuses smoke generation with those flags and writes a clear error:

```text
cached text embedding is not wired into WanI2VFast; refusing to fake T5 bypass
```

## Next Minimal Implementation

Only after the standalone T5 probe succeeds should we consider a minimal LingBot runtime patch that allows:

1. constructing `WanI2VFast` without loading T5, or
2. injecting precomputed text context into `generate`, or
3. replacing the T5 object with a small adapter that returns cached embeddings for fixed smoke prompts.

None of those are implemented in this pass.
