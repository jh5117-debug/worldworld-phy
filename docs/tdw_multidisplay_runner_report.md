# TDW Multidisplay Runner Report

Added `scripts/34_run_tdw_multidisplay_generation.sh`.

The runner:

- accepts one manifest;
- splits it into fixed-size chunks with `split_manifest_chunks.py`;
- assigns chunks round-robin to the requested display list;
- runs one TDW process per display/chunk;
- writes per-display/chunk logs;
- supports `--no_overwrite`;
- optionally validates each chunk;
- stops if chunk failure rate exceeds the configured threshold.

It has not been used for real multi-display TDW generation yet because the current extra displays are llvmpipe or unavailable, not NVIDIA GPU Xorg displays.
