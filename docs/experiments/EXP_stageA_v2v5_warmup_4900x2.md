# EXP StageA V2V-5 Warmup 4900x2

## Current Status

The requested full warmup is blocked by data availability. Current generated_v5 disk state contains only 3299 unique Stage1-ready clips, while the requested split requires 5000 unique clips.

## Goal

Run a prefix-aware LingBot-Fast StageA warmup using:

- train=4900
- test=100
- num_epochs=2
- H20 physical GPU4-7 only
- camera-conditioning LoRA rank 4
- prefix_len=5
- prediction_start_frame=5
- loss_frame_indices=5-80

## Why The Previous Run Was Small

The previous V2V-5 warmup was a pilot:

- 800 train rows, 100 val rows, 100 test rows
- 100 optimizer steps due `hard_max_optimizer_steps=100`
- camera-conditioning LoRA rank4 only
- used to verify prefix-aware future-only training and checkpoint eval, not to exhaust generated_v5.

## Data Gate

Required:

- 5000 unique Stage1-ready clips
- each clip contains `video.mp4`, `target.mp4`, `image.jpg`, `poses.npy`, `intrinsics.npy`, `prompt.txt`, and `metadata.json`

Observed on 2026-07-05:

- raw generated_v5 HDF5: 3999
- converted Stage1-ready unique clips: 3299
- shortfall: 1701

Gate result: `BLOCKED_INSUFFICIENT_STAGE1_READY_DATA`

## Prepared Implementation

- `cam_physgeo/data/build_v2v5_warmup_4900_split.py`
- `configs/cam_physgeo/fast_stageA_v2v5_camera_r4_4900x2.yaml`
- `scripts/launch_fast_stageA_v2v5_camera_r4_4900x2.sh`

The split builder refuses to create metadata unless enough unique clips exist. The launcher refuses to train unless metadata counts are exactly train=4900 and test=100.

## Step Count

For train=4900, num_epochs=2, gradient_accumulation_steps=1, and 4 GPUs:

- optimizer steps per epoch = ceil(ceil(4900 / 4) / 1) = 1225
- total optimizer steps = 2450

The config therefore sets high-branch min/target/hard_max optimizer steps to 2450.

## GPU Policy

Allowed: physical GPU4, GPU5, GPU6, GPU7
Forbidden: physical GPU0, GPU1, GPU2, GPU3

The launcher defaults to `CUDA_VISIBLE_DEVICES=4,5,6,7` and exits if GPU0-3 are included.

## Runtime Policy

The launcher exports `PYTHONNOUSERSITE=1` because normal LingBot conda Python site initialization currently hangs, while `PYTHONNOUSERSITE=1` succeeds. This also avoids the user-site transformers conflict introduced during VBench repair.

## Success Gate

Only launch when:

- train metadata rows = 4900
- test metadata rows = 100
- data roots are unique, non-duplicated Stage1-ready clips
- GPU4-7 are free
- no GPU0-3 usage
- no destructive changes

## Failure Gate

Do not launch if:

- fewer than 5000 unique Stage1-ready clips exist
- metadata rows are not exactly 4900/100
- training would require sample repetition to satisfy count
- GPU0-3 are needed
- Python runtime cannot start even with `PYTHONNOUSERSITE=1`

## What Is Not Run

- no DPO
- no SDPO
- no Linear-DPO
- no winner-anchor
- no StageB
- no GRPO
- no broad-LoRA
- no checkpoint deletion
- no large files pushed
