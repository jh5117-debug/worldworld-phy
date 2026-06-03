# TDW Generation v2 1-Sample Actual Report

## Status

Blocked. No TDW/Unity actual sample was generated in this run.

## Reason

The `warmup_mild` plan is now valid and stress-free, but actual TDW generation requires the configured display `:8`. The H20 process audit showed `:8` is configured through `tdw-xorg-gpu0.conf`, which likely uses GPU0. This task only allows GPU6/7 for smoke work and requires stopping before any non-6/7 GPU use.

Remote SSH was intermittent during syncing, but the remote actual-generation gate was eventually executed. The gate returned `status=blocked` before launching Unity.

## Planned 1-Sample Settings

- profile: `warmup_mild`
- camera set: `warmup_mild`
- allowed variants: `orbit_left_12`, `orbit_right_12`, `strafe_left_025`, `strafe_right_025`, `dolly_in_010`, `dolly_out_010`
- banned variants: lookaway/offscreen/reobserve/extreme
- output root: `local_assets/data/physion/generated_v2`

## Generated Artifacts

None.

## Validation

Validator was run after the blocked gate and found no generated HDF5 files:

- HDF5 count: 0
- validation ok count: 0
- suitable for warmup: 0

Validation report path on H20:

- `local_assets/data/physion/generated_v2/reports/validation_1sample.md`

## GPU Usage

Actual TDW/Unity generation was not started. The gate report recorded:

- `tdw_display`: `:8`
- `tdw_display_gpu_index`: 0
- allowed GPU indices: `[6, 7]`
- blocked reason: display GPU0 is outside the allowed GPU set.

A GPU approval/display request was written to `docs/gpu_usage_approval_request.md`.

## Continue To 10-Sample?

No. 10-sample smoke remains skipped until the 1-sample actual generation passes validation.
