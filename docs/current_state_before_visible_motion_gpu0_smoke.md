# Current State Before Visible-Motion GPU0 Smoke

Date: 2026-06-05

## Summary

The previous template-diverse 50-sample `warmup_mild` TDW batch passed the pipeline gates but was manually reassessed as too static for final camera-conditioned warmup data.

## Old 50-Sample Reassessment

- HDF5 / RGB / depth / ID / camera / object-state validation passed.
- LingBot cam-only conversion passed.
- `target.mp4` probe passed.
- `use_action=false` and dummy zero `action.npy` were correct.
- Camera motion was too weak by visual inspection.
- These 50 samples remain useful as pipeline validation data, but not as final warmup main data.

## Visible-Motion Profile

`warmup_visible_motion` exists and uses stronger but non-stress camera variants:

- `orbit_left_24`
- `orbit_right_24`
- `orbit_left_28`
- `orbit_right_28`
- `strafe_left_050`
- `strafe_right_050`
- `dolly_in_025`
- `dolly_out_025`

The profile keeps stress / reobserve camera variants banned:

- `lookaway`
- `offscreen`
- `relative_yaw_180`
- `reobserve`
- `occluder`
- `extreme`

## Validator

The visible-motion validator exists and checks:

- `camera_path_length`
- `yaw_change_proxy`
- `translation_magnitude`
- `background_motion_proxy`
- `parallax_proxy`
- `target_visible_ratio`
- `target_area_ratio_avg`
- `max_invisible_frames`
- `too_static`
- `too_extreme`
- `suitable_for_visible_motion`

## Approval

The user explicitly approved GPU0-bound `DISPLAY=:8` only for this run:

1. Run one `warmup_visible_motion` sample.
2. If it passes, run ten `warmup_visible_motion` smoke samples.
3. Do not run 50 / 200 / 1k.
4. Do not train or run DPO.

## Why Not 50

The current task is a smoke-quality gate. The 10-sample result must establish whether stronger camera motion is visible without becoming too static or too extreme before any 50-sample validation is requested.
