# StageA v5 Broad-LoRA PRD

## Goal

Run LingBot-Fast camera-conditioned StageA warmup on validated TDW / Physion v5 data using adapter-only training. The goal is to improve camera-conditioned global motion and foreground stability before any preference or DPO work.

## Non-Goals

- No DPO training.
- No reward scoring or reward calibration.
- No winner/loser pair construction.
- No StageB in this first broad-LoRA gate.
- No full model finetuning.
- No GPU0 use for LingBot training.

## Training Scope

LoRA must cover more than the small camera-only adapter. The required target groups are:

- camera conditioning / Plucker injection
- self-attention Linear layers
- cross-attention Linear layers
- FFN / MLP Linear layers

Training fails if any required group is empty.

## Data Requirements

The dataset must be Stage1-ready:

- `metadata_train.csv`
- `metadata_val.csv`
- per-clip `video.mp4`
- per-clip `poses.npy`
- per-clip `intrinsics.npy`
- prompt text that describes foreground, background, physics event, camera trajectory, and negative constraints

Raw HDF5 alone is insufficient for the current Stage1 trainer.

## Current Data Blocker

The active generated_v5 scale-up has HDF5 files but validation reports are blocked and conversion is not present. Formal training on generated_v5 should wait for validation + conversion.

## Minimal Safe Fallback

Use the existing TDW v5 1000 combined_prompt_v2 converted dataset for preflight and code validation only. Do not claim this is the final generated_v5 formal run.
