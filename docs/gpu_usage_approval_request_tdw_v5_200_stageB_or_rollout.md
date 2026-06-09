# GPU Approval Request: TDW v5 200 Stage B or Rollout

Date: 2026-06-09

## Current Gate

Stage A high-noise/global-camera warmup pilot passed:

- steps completed: 20
- train loss finite: yes
- val loss finite: yes
- trainable scope: `camera_control_lora_tiny`
- trainable parameters: 40,960
- LoRA tensors changed: 4
- sampled base tensors changed: 0
- no checkpoint / LoRA / optimizer state saved
- no DPO / rollout / reward calibration

Important limitation: the 20-step run consumed the first 20 rows in the train split order, which were all `collision + orbit_right_64`. The next pilot should shuffle or balance samples.

## Option 1: Stage B Mixed / Low-Noise Detail Pilot

Purpose: test whether a broader or low-noise timestep band remains stable while preserving camera-conditioned detail.

Proposed settings:

- GPU: GPU7 first, fallback GPU6/7 if needed
- max steps: 100
- batch size: 1
- frames: 8
- resolution: 480x832
- timestep mode: `mixed` or `low_noise`
- trainable scope: `camera_control_lora_tiny`
- sampler: shuffled / balanced by template and camera variant
- checkpoint: disabled unless separately approved
- no DPO
- no rollout
- no reward calibration

## Option 2: Rerun Stage A With Checkpoint/LoRA Save Enabled

Purpose: produce a tiny saved adapter so a later approved rollout can inspect whether camera response changed.

This requires explicit approval because the current safety policy forbids saving LoRA/checkpoint files.

## Option 3: Tiny Rollout From Stage A

Not possible from the completed run because no checkpoint or LoRA was saved. This option requires rerunning a short Stage A pilot with approved adapter saving first.

## Option 4: Pause and Inspect Metrics

The current metrics-only gate is enough to say the path is trainable and stable, but not enough to judge visual improvement.

## Required Approval

Please explicitly approve one next action before any further training, checkpoint save, rollout, reward calibration, or DPO work.
