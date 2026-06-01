# LingBot Model Forward Probe Report

## Result

- Status: passed.
- Winner forward: passed.
- Loser forward: passed.
- Prediction shape matches latent: true.
- Winner latent / pred shape: `[16, 2, 60, 104]`.
- Loser latent / pred shape: `[16, 2, 60, 104]`.
- Prediction dtype: `float32` output from `WanModelFast.forward`.
- NaN/Inf: none in winner or loser prediction.

## Target Context

The probe used the real LingBot flow target construction, but did not compute
energy in this mode:

- Target type: `flow_velocity_noise_minus_x0`.
- Formula: `target = noise - x0`.
- Noisy latent: `x_t = (1 - sigma) * x0 + sigma * noise`.
- Sigma in this run: `0.17600001394748688`.
- Evidence: `scripts/train_lingbot_physics_predictor.py::sample_flow_batch`.

## Condition

- Control type: `cam`.
- Camera/control tensor shape: `[1, 384, 2, 60, 104]`.
- Control tensor dtype/device: `bfloat16` on `cuda:0`.
- Image condition tensor shape: `[20, 2, 60, 104]`.
- Text context shape: `[47, 4096]`.
- `seq_len`: `12480`.
- `kv_size`: `3120`.
- `use_action=false`: preserved.
- Dummy action norm: `0.0`.

## Adapter Fixes Needed During Probe

The probe exposed and fixed three wrapper bugs:

- T5 text encoder is CPU by default, so prompt encode now runs on CPU and moves
  context to GPU afterward.
- I2V mask must have 4 channels, not 1, so image condition is
  `4 mask + 16 VAE latent = 20` channels.
- LingBot cache initializers use positional args `(num_layers, shape, dtype, device)`.
- Forward must be wrapped in `torch.amp.autocast("cuda", dtype=param_dtype)`,
  matching `WanI2VFast.generate`.

## Safety

No loss, backward, optimizer, LoRA, or parameter update was run.
