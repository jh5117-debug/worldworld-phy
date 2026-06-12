# TDW v5 Real Warmup Dataset Selection Report

Date: 2026-06-11

## Selected Dataset

Using existing TDW v5 aggressive 2x human-approved 200 dataset.

## Reason

TDW 1k generation is blocked by display/GPU approval. The existing v5 200 dataset has already passed:

- data integrity audit;
- target.mp4 probe;
- train/val/test split;
- LingBot dataloader smoke;
- true LingBot-Fast forward-loss gate.

## Split Distribution

Remote split check:

- train: 160 samples
  - collision: 48
  - drop: 48
  - roll: 32
  - containment: 32
- val: 20 samples
  - collision: 6
  - drop: 6
  - roll: 4
  - containment: 4
- test: 20 samples
  - collision: 6
  - drop: 6
  - roll: 4
  - containment: 4

Main camera variants observed:

- `orbit_left_72`
- `orbit_left_44`
- `orbit_right_60`
- `orbit_right_64`
- `strafe_left_180`

## Warmup Choice

Stage A uses balanced sampling over `template,camera_variant`. For 300 steps on 160 training samples, the sampler intentionally switches to replacement sampling across epochs while preserving balanced template coverage.
