# TDW v5 1k Profile / Code Audit Report

Date: 2026-06-14

## Profile

The scale-up used the already human-approved profile:

- `warmup_visible_motion_v5_aggressive_2x_demo`

This profile is the aggressive visible-motion version selected after the earlier v3/v4/v5 demo review. It starts camera motion at frame 0 and uses stronger camera movement than the earlier v2/v3 review sets.

## Code Changes Used For Scale-Up

The generation tools were updated to support non-overlapping scale-up generation:

- `plan_trials.py`
  - `--start_index`
  - `--seed_start`
  - `--output_tag`
  - `--raw_output_subdir`
- `run_tdw_trial.py`
  - uses `sample_index` for output naming and ports
  - supports manifest-level `output_subdir`
  - keeps `--no_overwrite`
- `validate_generated_hdf5.py`
  - resolves HDF5 paths using `sample_index` and `output_subdir`
- `convert_generated_to_lingbot.py`
  - resolves HDF5 paths using `sample_index` and `output_subdir`
  - adds `--validation_json` so conversion can use the intended validation report explicitly
- `build_lingbot_dataset_manifest.py`
  - supports multiple roots through `--roots`
- `audit_lingbot_dataset.py`
  - adds imageio fallback video probing when ffprobe/cv2 are unavailable
- `split_manifest_chunks.py`
  - splits a JSONL generation plan into fixed-size chunk manifests

## Safety

The code changes are scoped to TDW generation, validation, conversion, manifest, and audit tools. No training or DPO code path was executed.

