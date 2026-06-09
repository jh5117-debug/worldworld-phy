# GPU Approval Request: TDW v5 200 Stage B or Rollout

Date: 2026-06-09

## Current Gate

The original Stage A high-noise/global-camera warmup pilot passed as a stability smoke, but its first 20 rows were all `collision + orbit_right_64`.

The balanced Stage A rerun now also passes:

- steps completed: `60`;
- train sampler: balanced by `template,camera_variant`;
- first 20 templates: `drop:5`, `collision:5`, `roll:5`, `containment:5`;
- full 60 templates: `drop:15`, `collision:15`, `roll:15`, `containment:15`;
- train loss finite: yes;
- val loss finite: yes;
- trainable scope: `camera_control_lora_tiny`;
- trainable parameters: `40,960`;
- LoRA tensors changed: `4`;
- sampled base tensors changed: `0`;
- one tiny adapter checkpoint saved;
- no full model checkpoint;
- no optimizer state;
- no DPO / rollout / reward calibration.

Adapter checkpoint:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

Size: `166,809` bytes.

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

## Option 2: Tiny Rollout From Balanced Stage A Adapter

Purpose: inspect whether the balanced Stage A adapter changes camera response and background stability.

Proposed settings:

- GPU: GPU7 first, fallback GPU6/7 if needed;
- samples: 4 total, one per template;
- compare base LingBot-Fast vs Stage A balanced adapter;
- output videos only;
- no DPO;
- no reward calibration;
- no training.

## Option 3: Stage B Mixed / Low-Noise Detail Pilot After Rollout

Only consider this if the rollout smoke shows useful camera-conditioned behavior.

## Option 4: Pause and Inspect Metrics

The current metrics-only gate is enough to say the path is trainable and stable, but not enough to judge visual improvement.

## Required Approval

Please explicitly approve one next action before any further training, rollout, reward calibration, or DPO work.
