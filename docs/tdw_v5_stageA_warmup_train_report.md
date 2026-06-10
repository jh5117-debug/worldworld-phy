# TDW v5 Stage A Warmup Train Report

Date: 2026-06-10

## Current Warmup Status

The previous balanced Stage A high-noise warmup remains the active adapter checkpoint.

- steps: 60/60;
- train loss: 0.065782 -> 0.053271;
- val loss: 0.037449 / 0.046542 / 0.057670;
- timestep: diagnostic high-noise, timestep 799, sigma 0.799;
- trainable scope: `camera_control_lora_tiny`;
- LoRA target modules: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`;
- checkpoint: adapter-only, 166,809 bytes;
- no full model checkpoint;
- no optimizer state.

## Why 300-Step Warmup Was Not Run

The previous 60-step run took about 9028 seconds. A 300-step run is expected to exceed 12 hours. The request explicitly says steps expected to require more than 12 hours need an approval request first.

## Recommended Next

Do not run longer warmup before rollout inspection. First run a small base-vs-Stage-A-adapter rollout smoke, then decide whether Stage A should be extended, moved to Stage B, or retargeted.
