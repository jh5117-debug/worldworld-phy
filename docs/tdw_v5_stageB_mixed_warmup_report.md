# TDW v5 Stage B Mixed Warmup Report

Date: 2026-06-12

## Purpose

Stage B was a small mixed-timestep refinement run initialized from the formal Stage A adapter. It was not DPO and did not run rollout or reward during training.

## Configuration

- Init adapter:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/warmup_stageA_resume/checkpoint/stageA_high_noise_camera_lora_final`
- Timestep mode: mixed diagnostic high-noise / low-noise / random.
- Trainable scope: `camera_control_lora_tiny`.
- Batch size: 1.
- Steps: 200.
- Learning rate: 5e-6.
- Frames / resolution: 8 frames at 480x832.
- No DPO.
- No VideoGPA 03_train.
- No full model checkpoint.
- No optimizer state.

## Result

- Status: passed.
- Steps completed: 200 / 200.
- Train loss first / last / min / max: 0.012603 / 0.653122 / 0.006603 / 1.173266.
- Val loss: 0.649436, 0.012918, 0.008798, 0.726406.
- Band counts:
  - diagnostic_high_noise_quantile: 67
  - diagnostic_low_noise_quantile: 67
  - random: 66
- NaN / Inf: none.
- OOM: none.

The higher low-noise losses are expected to be less directly comparable with the high-noise Stage A losses because this run intentionally mixes diagnostic bands.

## Checkpoint

- Final Stage B adapter:
  `local_assets/experiments/exp_tdw_v5_real_scale_warmup_reward_pairs/warmup_stageB/checkpoint/stageB_mixed_camera_lora_final/adapter_state.pt`
- Size: 166,809 bytes.
- Contents: adapter-only LoRA tensors.
- Full model checkpoint: no.
- Optimizer state: no.

## Gate

Stage B is considered training-stability passed. Quality must be judged by rollout and reward, not by loss alone.

