# TDW Multidisplay Runner Sanity Report

## Runner files

- `scripts/34_run_tdw_multidisplay_generation.sh` exists.
- `cam_physgeo/data/tdw_generation_v2/split_manifest_chunks.py` exists.
- `cam_physgeo/data/tdw_generation_v2/run_multidisplay_generation.py` exists as a Python wrapper.

## Sanity checks

- `bash -n scripts/34_run_tdw_multidisplay_generation.sh`: passed.
- Python compile checks for runner/prompt audit tools: passed.

## Safety update

The shell runner now accepts `--reject_llvpipe true`. When enabled, it checks `xdpyinfo` and `glxinfo -B` for every requested display and refuses to run if the renderer is not NVIDIA or contains llvmpipe.

## Port support

The repository search found TDW/Controller references, but no clean, verified per-process port argument has been wired into this runner yet. Until explicit port support is confirmed in the active TDW runner, multidisplay smoke should stay small and use staggered/chunked process launches with per-display logs.
