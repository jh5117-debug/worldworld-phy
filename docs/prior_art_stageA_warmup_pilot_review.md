# Prior-Art Review: Stage A Warmup Pilot

Date: 2026-06-09

## Existing Entrypoints

The codebase did not previously expose a completed `staged_warmup_pilot` training mode. The closest prior art is:

- `cam_physgeo/training/lingbot_warmup_smoke.py`: component-load and true forward-loss dry-run.
- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`: real LingBot-Fast load, VAE load, camera condition construction, timestep/noise handling, LoRA target resolution, and prior DPO dry-run utilities.
- `cam_physgeo/dpo/lora_utils.py`: runtime LoRA module injection, parameter counting, and base-freeze helpers.

## Reused Hooks

The Stage A pilot reuses existing adapter functionality rather than writing a separate LingBot training stack:

- `LingBotFastVideoGPAAdapter.load_policy_model`
- `LingBotFastVideoGPAAdapter.load_vae`
- `LingBotFastVideoGPAAdapter._build_forward_condition`
- `LingBotFastVideoGPAAdapter._model_forward_once`
- `LingBotFastVideoGPAAdapter._resolve_lora_targets`
- `LingBotFastVideoGPAAdapter._select_trainable_params`
- `inject_lora_into_modules`
- `freeze_non_lora_parameters`

This preserves the same camera-control tensor path used by the true forward-loss smoke.

## Trainable Scope

Supported prior-art scopes include:

- `camera_adapter`
- `lora`
- `camera_lora_tiny`
- `camera_control_lora_tiny`
- `qkv_lora_tiny`

For this pilot, only `camera_control_lora_tiny` is enabled. The pilot injects runtime rank-2 LoRA into the resolved camera/control targets, freezes all non-LoRA parameters, and rejects any non-LoRA trainable parameter selection.

## Timestep Mode

The prior true forward-loss smoke used scheduler-quantile diagnostic timestep bands:

- diagnostic high-noise: timestep 799, sigma about 0.799
- diagnostic low-noise: timestep 200, sigma about 0.200
- random: sampled uniformly

LingBot-Fast did not expose explicit expert routing in the previous smoke, so Stage A uses `high_noise` as a scheduler diagnostic band, not as an exact MoE expert-boundary claim.

## Checkpoint and Output Policy

The pilot is metrics-only:

- no checkpoint save
- no LoRA save
- no optimizer state save
- no rollout
- no reward calibration
- no DPO

The optimizer is used only in-memory over the runtime LoRA parameters.

## Minimal Change

`cam_physgeo/training/lingbot_warmup_smoke.py` was extended with `--mode staged_warmup_pilot` and related safety flags. No third-party LingBot files or base weights were modified.
