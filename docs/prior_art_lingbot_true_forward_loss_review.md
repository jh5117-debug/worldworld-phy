# Prior Art: LingBot True Forward-Loss Path

Date: 2026-06-09

## Local Evidence

The real model path is already implemented in `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`.

Relevant pieces:

- `LingBotFastVideoGPAAdapter._load_fast_pipeline(...)` imports LingBot runtime modules and creates `WanI2VFast`.
- `load_policy_model(..., dry_run=False)` freezes the policy model and sets eval mode.
- `load_vae(..., dry_run=False)` loads the Wan/LingBot VAE.
- `_build_forward_condition(...)` builds prompt context, image condition latent, and camera Plücker/control tensors from `poses.npy` and `intrinsics.npy`.
- `_flow_noisy_and_target(...)` defines `z_t = (1 - sigma) * x0 + sigma * noise` and target `noise - x0`.
- `_model_forward_once(...)` calls the real `pipe.model(...)` with no grad.

## True Smoke Implementation

`cam_physgeo/training/lingbot_warmup_smoke.py` now reuses the above path instead of inventing a parallel warmup forward. The new modes are:

- `component_load_smoke`: tokenizer/T5 path, LingBot-Fast policy, VAE, scheduler, and model inspection.
- `true_forward_loss_dryrun`: dataloader sample -> target video -> real VAE latent -> prompt/image/camera condition -> timestep/noise -> policy forward -> MSE against flow target.

## No Placeholder Rule

If `--require_real_model_load true` is set, the script must return failure if it cannot load the real LingBot-Fast policy/VAE path. Placeholder tensor allocation is marked `failed_not_real_model_load` for this gate.

## Forward Target

Target type used in the smoke:

`flow_velocity_noise_minus_x0`

Formula:

`sigma = timestep / num_train_timesteps`

`z_t = (1 - sigma) * x0 + sigma * noise`

`target = noise - x0`

This matches the local adapter and prior LingBot/Wan flow-matching audit docs.
