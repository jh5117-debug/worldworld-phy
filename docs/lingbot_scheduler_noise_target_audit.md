# LingBot Scheduler / Noise / Target Audit

## Scheduler

LingBot-Fast inference constructs a `FlowUniPCMultistepScheduler` and calls
`set_timesteps(...)` before generation. During denoising, it forwards a latent
through the model and then converts the flow prediction to `x0`.

## Target Type

The real target for the dry-run is flow / velocity:

```text
target = noise - x0
```

Evidence:

- `wan/image2video_fast.py::_convert_flow_pred_to_x0` states that the model
  predicts `noise - x0`.
- `scripts/train_lingbot_physics_predictor.py::sample_flow_batch` builds
  `z_t = (1 - sigma) * x0 + sigma * noise` and returns
  `target = noise - x0`.
- VideoGPA's Wan2.2 TI2V trainer uses the same velocity form for winner/loser
  preference training.

## Timestep / Sigma

For this dry-run the adapter follows the local LingBot training script:

```text
sigma = timestep / num_train_timesteps
x_t = (1 - sigma) * x0 + sigma * noise
target = noise - x0
```

This is code-backed for the local LingBot physics predictor. The inference
scheduler's shifted sigmas are still relevant for sampling, but the local
training target evidence is stronger for the no-training energy probe.

## Same Noise / Same Timestep

The previous batch dry-run confirmed same-noise and same-timestep at summary
level. The adapter now also saves local `batch_tensors.pt` under
`local_assets/outputs/...` so the forward/energy probe can reuse the same
actual noise and timestep tensors. These tensors remain untracked and must not
be committed.

## What Is Not Done

- No DPO loss is computed.
- No backward pass is run.
- No optimizer or LoRA state is created.
- Reference energies are deferred unless a second frozen LingBot model is
  explicitly loaded later.
