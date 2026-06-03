# TDW Generation v2 Mild Camera Patch Report

## Summary

Implemented an explicit `warmup_mild` camera set for TDW / Physion-style moving-camera v2 generation. The warmup profile now has a hard allow-list, a banned-keyword safety check, and an upstream runner mapping that avoids stress/reobserve leakage.

## New Camera Set

`camera_set: warmup_mild`

Allowed variants:

- `orbit_left_12`
- `orbit_right_12`
- `strafe_left_025`
- `strafe_right_025`
- `dolly_in_010`
- `dolly_out_010`

## Banned Variants / Keywords

Warmup generation refuses variants containing:

- `lookaway`
- `offscreen`
- `relative_yaw_180`
- `relative_lookaway`
- `reobserve`
- `occluder`
- `extreme`

## Upstream Argument Mapping

| v2 variant | upstream motion | orbit | strafe | radius | height |
|---|---|---:|---:|---:|---:|
| `orbit_left_12` | `orbit` | -12.0 | 0.0 | 0.0 | 0.02 |
| `orbit_right_12` | `orbit` | 12.0 | 0.0 | 0.0 | 0.02 |
| `strafe_left_025` | `strafe` | 0.0 | -0.25 | 0.0 | 0.02 |
| `strafe_right_025` | `strafe` | 0.0 | 0.25 | 0.0 | 0.02 |
| `dolly_in_010` | `orbit` | 0.0 | 0.0 | -0.10 | 0.01 |
| `dolly_out_010` | `orbit` | 0.0 | 0.0 | 0.10 | 0.01 |

The dolly variants use the existing upstream radius-delta path rather than requiring a new upstream `camera_motion` name.

## Implementation

Updated:

- `configs/cam_physgeo/tdw_generation_v2.yaml`
- `cam_physgeo/data/tdw_generation_v2/generation_config.py`
- `cam_physgeo/data/tdw_generation_v2/plan_trials.py`
- `cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py`

The runner now generates a local wrapper script under the output `logs/` directory. This wrapper imports the upstream batch runner, replaces its in-memory `CAMERA_VARIANTS` with the mild-only list, and calls upstream `main()`.

## Why Safe For Warmup

The selected variants are small yaw, small strafe, or small radius changes. They avoid lookaway, offscreen, 180-degree reobserve, occluders, and extreme rotations. They are intended to keep the target object visible and to avoid the old stress-sample failure mode where the foreground disappears for long stretches.

## Remaining Risk

Actual TDW/Unity execution may require the configured display `:8`. The current observed Xorg process is configured for GPU0, while this task allows only GPU 6/7. Actual generation must stay blocked unless a GPU 6/7 TDW display is available or the user explicitly approves a different GPU configuration.

## GPU Usage Assessment

- Plan dry-run: no GPU.
- HDF5 validation/contact sheet: expected no GPU.
- TDW/Unity actual generation: may use graphics GPU through `DISPLAY=:8`; currently likely GPU0.
- 50-sample validation/generation: requires a separate resource check and likely user confirmation if TDW uses GPU for more than a short smoke.

