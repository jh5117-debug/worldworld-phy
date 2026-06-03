# TDW Generation v2 LingBot Conversion Report

## Status

Skipped.

## Reason

No accepted v2 generated samples exist yet. Conversion to LingBot cam-only inputs is gated on successful HDF5 validation and filtering.

## Expected Output Structure When Enabled

Each accepted sample should include:

- `image.jpg`
- `target.mp4`
- `poses.npy`
- `intrinsics.npy`
- `prompt.txt`
- `metadata.json`
- optional `depth.npy`
- optional `id_mask.npy`
- dummy `action.npy`
- `use_action=false`

