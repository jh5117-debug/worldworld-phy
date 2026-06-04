# TDW Generation v2 Non-Drop Wrapper Fix Report

Date: 2026-06-04

## Root Cause

The wrapper called the upstream Physion runner with `cwd` set to the upstream workspace, while `--dir` was a relative `local_assets/...` path. As a result, non-drop HDF5 files were written under the upstream workspace instead of the project output tree.

Earlier fixes were necessary but not sufficient:

- drop-only args are now restricted to `template == "drop"`;
- actual generation commands include `--run 1`;
- non-drop templates receive upstream-style template-specific args.

The final missing fix was absolute output directory handling.

## Files Changed

- `cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py`
  - adds non-drop template-specific native args;
  - resolves per-trial `--dir` to an absolute path;
  - creates the per-trial output directory before subprocess launch.
- `cam_physgeo/data/tdw_generation_v2/convert_generated_to_lingbot.py`
  - maps manifest suffixes such as `plan_warmup_mild_template_diverse_10_fix.jsonl` to `validation_template_diverse_10_fix.json`.
- `cam_physgeo/utils/video.py`
  - adds an `imageio` fallback to `probe_video` so MP4 probing works in the TDW env without `cv2` or system `ffprobe`.

## Before / After

Before:

`--dir local_assets/data/physion/generated_v2/...`

When launched from upstream cwd, this wrote into the upstream workspace.

After:

`--dir /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/data/physion/generated_v2/...`

The wrapper now writes to the project `local_assets` tree.

## Remaining Risk

This validates a small smoke scale only. Larger 50/200/1k generation still requires staged approval and should not start automatically.

