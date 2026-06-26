# EXP Prefix-Aware V2V Conditioning

Status: planned

## Question

Does providing multiple clean prefix frames improve identity persistence, camera following, and reobserve consistency compared with single-frame I2V?

## Prefix Modes

- I2V-1: `prefix_len=1`
- V2V-5: `prefix_len=5`
- V2V-8: `prefix_len=8`
- V2V-16: `prefix_len=16`

## Data Contract

The prefix frames are conditioning input only. Loss, reward, DPO energy, and main metrics are computed only on the future segment after the prefix.

For `prefix_len=5`, frames `0..4` are condition frames and frame `5` is the first predicted/evaluated frame.

## Implementation Requirements

- Manifest fields: `prefix_len`, `prediction_start_frame`, `target_frame_indices`, `loss_frame_indices`, `reward_frame_indices`
- Condition mask must expose prefix latent frames and hide future latent frames.
- Loss/reward masks must exclude prefix frames.
- Poses and intrinsics stay aligned to the full 81-frame timeline.

## First Experiment

Run screen16 inference for:

- Original Fast
- selected small-LoRA candidate
- old tiny camera LoRA if safely loadable

Modes:

- I2V-1
- V2V-5
- V2V-8

## Decision

Choose DPO default prefix length based on future-only metrics and Codex visual audit, not on prefix reconstruction.

