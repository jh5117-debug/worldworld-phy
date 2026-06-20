# StageA v5 Data Snapshot

Date: 2026-06-20

## Intended Source

The requested StageA v5 snapshot source is the active TDW generated_v5 scale-up:

`local_assets/data/physion/generated_v5/raw_hdf5/v5_aggressive_2x_scaleup_4000_to_5000/`

The active generation is protected and continues in tmux on GPU0 / DISPLAY=:8. StageA warmup must not touch GPU0.

## Snapshot Rule

Only completed, validated, stable chunks may enter the immutable training snapshot. Active chunks and chunks whose validation reports are blocked must be excluded from formal StageA training.

## Current Validation Status

Inspection of `validation_chunk_000.md` shows:

- Generated HDF5 count: 100
- Validation ok count: 0
- Suitable for warmup count: 0
- Suitable for visible motion count: 0
- Row status: `blocked`

The generated_v5 directory currently has raw HDF5 files but no Stage1-ready converted files:

- `target.mp4`: 0 under generated_v5
- `video.mp4`: 0 under generated_v5
- `poses.npy`: 0 under generated_v5
- `intrinsics.npy`: 0 under generated_v5

## Current Decision

generated_v5 is not yet ready for formal StageA training. The code now includes `cam_physgeo.data.build_stageA_v5_snapshot`, which records blocked status instead of silently accepting samples.

For a runnable Stage1 dataset today, use the already converted 1000-sample prompt_v2 LingBot manifest and prepare it with `cam_physgeo.data.prepare_stage1_dataset_from_lingbot_manifest`.

## Required Next Data Action

1. Repair or rerun generated_v5 validation so completed chunks report nonzero validation-ok counts.
2. Convert accepted generated_v5 samples to LingBot cam-only format.
3. Build a Stage1 dataset directory from validated converted manifests.
4. Only then launch formal generated_v5 StageA training.
