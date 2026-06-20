# StageA v5 Training Report

Date: 2026-06-20

## Status

Formal generated_v5 StageA training was not launched.

## Why It Did Not Launch

The current user requirement says formal StageA must use completed validated generated_v5 data. The generated_v5 raw HDF5 scale-up is still active and its validation reports currently show:

- Generated HDF5 exists.
- Validation ok count is 0.
- Samples are marked `blocked`.
- No generated_v5 LingBot conversion outputs exist yet (`target.mp4`, `poses.npy`, `intrinsics.npy`).

Therefore generated_v5 is not yet a valid Stage1 training source.

## What Was Completed Instead

- Broad-LoRA implementation repaired.
- Optimizer-step semantics repaired.
- Adapter-only checkpoint metadata added.
- Stage1 dataset preparation tool added.
- Existing 1000 combined_prompt_v2 converted dataset prepared successfully for Stage1 fallback/preflight.
- generated_v5 snapshot tool added and used to prove validated-only count is 0.

## Next Training Gate

Before formal StageA training:

1. Repair or rerun generated_v5 validation.
2. Convert accepted generated_v5 HDF5 samples to LingBot cam-only format.
3. Prepare Stage1 dataset CSV/clip directory from the converted manifest.
4. Run GPU preflight on GPU7.
5. Launch formal low/high StageA only if preflight passes.
