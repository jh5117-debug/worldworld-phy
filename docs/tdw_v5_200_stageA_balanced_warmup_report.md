# TDW v5 200 Stage A Balanced Warmup Report

Date: 2026-06-09

## Result

Status: passed.

This rerun fixed the previous Stage A sampling caveat. The prior 20-step pilot proved the real warmup path was stable, but all 20 samples were `collision + orbit_right_64`. The balanced pilot completed `60 / 60` high-noise Stage A steps and covered all four templates.

## Setup

- Dataset: TDW v5 aggressive 2x 200 human-approved set.
- Train split: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/train.jsonl`.
- Val split: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/val.jsonl`.
- GPU: GPU7 only; GPU0 was not used.
- Model: real LingBot-Fast runtime, `WanI2VFast` / `WanModelFast`.
- VAE: `Wan2_1_VAE`.
- Trainable scope: `camera_control_lora_tiny`.
- LoRA targets: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Trainable params: `40,960`.
- Optimizer: AdamW, one param group, LoRA params only.
- Timestep band: diagnostic high-noise scheduler quantile.
- Timestep / sigma: `799 / 0.799`.

## Sampler Coverage

Sampler: `balanced`.

Balance keys: `template,camera_variant`.

Shuffle seed: `123`.

First 20 train steps:

| Template | Count |
|---|---:|
| drop | 5 |
| collision | 5 |
| roll | 5 |
| containment | 5 |

All 60 train steps:

| Template | Count |
|---|---:|
| drop | 15 |
| collision | 15 |
| roll | 15 |
| containment | 15 |

Camera variants across all 60 train steps:

- `orbit_left_72`: 15
- `strafe_left_180`: 8
- `orbit_right_60`: 15
- `orbit_left_44`: 15
- `orbit_right_64`: 7

Duplicate train sample count: `0`.

Note: validation sampling was still sequential from the val split, so the three validation probes were `collision + orbit_right_64`. This is acceptable for this Stage A train-sampler gate but should be balanced for Stage B or rollout comparisons.

## Metrics

Steps completed: `60`.

Train loss:

- first: `0.065782`
- last: `0.053271`
- min: `0.033201`
- max: `0.067220`

Validation loss:

- step 20: `0.037449`
- step 40: `0.046542`
- step 60: `0.057670`

Gradient norm:

- first: `0.002388`
- last: `0.007207`
- max: `0.012527`

All train and val losses were finite. There was no NaN, Inf, or OOM.

LoRA tensors changed: `4`.

Sampled frozen base tensors changed: `0`.

## Checkpoint

Exactly one tiny adapter checkpoint was saved:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

Checkpoint size: `166,809` bytes (`0.1591` MB).

Contents:

- `blocks.39.cam_scale_layer.lora_A`
- `blocks.39.cam_scale_layer.lora_B`
- `blocks.39.cam_shift_layer.lora_A`
- `blocks.39.cam_shift_layer.lora_B`

The checkpoint contains only LoRA / adapter weights. It does not contain full model weights or optimizer state.

## Safety

- No DPO training.
- No VideoGPA `03_train`.
- No Stage1.
- No rollout.
- No reward calibration.
- No TDW generation.
- No full model checkpoint.
- No optimizer state.
- No local_assets files are part of the Git commit.

## Gate

Stage A balanced warmup passed.

The next allowed action is a user-approved rollout smoke using the saved adapter, or a separate Stage B approval. Do not run rollout, Stage B, reward calibration, or DPO without explicit approval.
