# TDW Multidisplay Scaleup Decision Report

## Decision

Do not generate additional TDW data in this round.

## Reason

The NVIDIA multi-display smoke did not run because only `DISPLAY=:8` is a valid NVIDIA display. The other currently reachable displays are llvmpipe or unavailable.

## If smoke passes later

Recommended staged scale-up:

1. Current: 1000 valid samples.
2. Add +1000 first, reaching 2000 total.
3. Audit HDF5, conversion, prompt-v2 manifest, split, scene diversity, and review subset.
4. Only after that, consider +3000 to reach 5000.

Do not jump directly to 5000/10000.

## Draft +1000 command

After display setup and smoke pass, generate a new plan with unique start_index/seed_start and run `scripts/34_run_tdw_multidisplay_generation.sh` with only verified NVIDIA displays and `--reject_llvpipe true`.
