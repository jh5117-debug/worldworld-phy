# Small-LoRA Scope Sweep Preflight Report

Updated: 2026-06-24 13:20 CST

## Current status

Status: PRECHECK DATA GATE FIXED, PREFLIGHT RETRY REQUIRED.

The first four 2-GPU small-LoRA preflights did not reach optimizer steps. All four runs loaded LingBot-World-Fast and applied the intended LoRA scopes, then failed at dataloader video decode.

## Root cause

The Stage1 dataset preparation helper only accepted `target_video_path` / `video_path`, `poses_path`, and `intrinsics_path`. The generated_v5 fullprep manifest uses `target_video`, `poses`, and `intrinsics`. Empty paths were resolved to `Path("")`, which exists as the current directory, so the helper created symlinks pointing to `.`:

- `video.mp4 -> .`
- `poses.npy -> .`
- `intrinsics.npy -> .`

The dataloader then tried to decode a directory as a video and failed with `Could not decode any frame`.

## Fix

`cam_physgeo/data/prepare_stage1_dataset_from_lingbot_manifest.py` now:

- supports generated_v5 keys: `target_video`, `poses`, `intrinsics`;
- treats empty path fields as missing instead of current directory;
- requires source paths to be files, not directories;
- reads prompt text when `prompt` contains a path to `prompt.txt`;
- keeps the old key names for compatibility.

## Fixed snapshot

Prepared dataset:

`local_assets/experiments/small_lora_scope_sweep_20260624/stage1_dataset_fullprep_20260624_0152_fixed/`

Counts:

- train: 2804 / 2804 prepared
- val: 329 / 329 prepared
- test: 166 / 166 prepared

Smoke checks passed for sampled train/val/test rows:

- `video.mp4` resolves to converted generated_v5 video files;
- frame 0 decodes as 480x832 RGB;
- `poses.npy` shape is `(81, 4, 4)` and finite;
- `intrinsics.npy` shape is `(81, 4)` and finite;
- `prompt.txt` contains structured prompt text, not a file path.

## LoRA scope sanity from failed preflight

The failed preflight still confirmed module matching:

- A camera-only rank4: 160 camera conditioning Linear layers, 6,553,600 trainable params.
- B camera-only rank8: 160 camera conditioning Linear layers, 13,107,200 trainable params.
- C camera + limited self-attention rank4: 32 Linear layers in blocks 36-39, 1,310,720 trainable params.
- D camera + limited cross-attention rank4: 32 Linear layers in blocks 36-39, 1,310,720 trainable params.

These are all far below the failed broad-LoRA 102,891,520-param run.

## Next action

Rerun the same four 2-GPU 5-step preflights using the fixed snapshot. If all pass, launch the 200-step small-LoRA sweep.
