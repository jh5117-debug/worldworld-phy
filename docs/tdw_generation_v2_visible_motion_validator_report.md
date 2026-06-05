# TDW v2 Visible-Motion Validator Report

Date: 2026-06-05

## Metrics Added

`validate_generated_hdf5.py` now reports additional motion-quality fields:

- `camera_path_length`
- `camera_translation_total`
- `camera_step_max`
- `yaw_change_proxy`
- `yaw_path_proxy`
- `video_motion_proxy`
- `background_motion_proxy`
- `parallax_proxy`
- `too_static`
- `too_extreme`
- `suitable_for_visible_motion`
- `motion_rejection_reasons`

## Proxy Definitions

The new background/parallax checks are lightweight and do not use RAFT.

- `video_motion_proxy`: mean normalized RGB difference over sampled frames.
- `background_motion_proxy`: same proxy on top/side image regions to reduce foreground dominance.
- `parallax_proxy`: currently the same lightweight background-motion proxy.
- `yaw_change_proxy`: yaw change computed from `camera_position` and `camera_aim`.

## Acceptance Logic

For `--profile warmup_visible_motion`:

`too_static = true` if:

- `camera_path_length < 0.45`; or
- `background_motion_proxy < 0.012`; or
- `video_motion_proxy < 0.015`.

`too_extreme = true` if:

- `target_visible_ratio < 0.75`; or
- `max_invisible_frames > 8`; or
- `camera_path_length > 1.50`.

`suitable_for_visible_motion = true` only if the sample is neither too static nor too extreme.

## Why The Old 50 Is Too Weak

The old 50-sample batch used:

- 12-degree orbit;
- 0.25 strafe;
- 0.10 dolly.

Those settings can pass schema and visibility validation while still producing videos that look almost static. The new validator explicitly distinguishes pipeline validity from visible camera-motion quality.

## Filter Integration

`filter_generated_samples.py` now accepts `--profile warmup_visible_motion` and rejects samples marked:

- `too_static`
- `too_extreme`
- `not_suitable_for_visible_motion`

`make_generation_contact_sheet.py` can summarize visible-motion suitability when provided a validation JSON.
