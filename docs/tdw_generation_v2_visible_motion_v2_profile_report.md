# TDW Generation v2 Visible-Motion v2 Profile Report

Date: 2026-06-05

## Why v1 Only Passed 5/10

`warmup_visible_motion` v1 used one global camera variant cycle for all templates. That caused mismatches:

- `drop` handled orbit 24/28 well.
- `collision` handled strafe 0.50 well, but orbit 28 exceeded the camera-path threshold.
- `roll` received dolly 0.25, which was too static.
- `containment` received orbit 24, which exceeded the camera-path threshold.

The issue is profile design, not HDF5/key completeness: all 10 v1 samples passed HDF5 validation.

## v2 Profile

New profile:

```text
warmup_visible_motion_v2
```

Core change:

```text
template_camera_variants
```

This lets the planner choose camera variants based on the scene template.

## Template-Aware Camera Choices

| Template | v2 allowed choices | Avoided |
|---|---|---|
| drop | `orbit_left_24`, `orbit_right_24`, `orbit_left_28`, `orbit_right_28` | none from v1 accepted set |
| collision | `strafe_left_050`, `strafe_right_050`, `orbit_left_24`, `orbit_right_24` | orbit 28 |
| roll | `strafe_left_050`, `strafe_right_050`, `orbit_left_24`, `orbit_right_24` | dolly 0.25 |
| containment | `orbit_left_18`, `orbit_right_18`, `orbit_left_20`, `orbit_right_20`, `strafe_left_050`, `strafe_right_050` | orbit 24 / 28 |

## Thresholds

Validator thresholds remain unchanged:

- `target_visible_ratio >= 0.75`
- `max_invisible_frames <= 8`
- `min_camera_path_length >= 0.45`
- `max_camera_path_length <= 1.50`
- `background_motion_proxy >= 0.012`
- `video_motion_proxy >= 0.015`

## Expected Acceptance

Expected acceptance should improve from 5/10 to at least 8/10 if template-specific choices work:

- drop should remain accepted;
- collision should avoid the known orbit-28 failure;
- roll should avoid the dolly-too-static failure;
- containment should avoid the orbit-24 too-extreme failure.

## Risks

- strafe on roll might still be scene-dependent and could cause target framing issues.
- containment orbit 18/20 might still be too strong or too weak depending on scene scale.
- Acceptance still requires actual TDW validation; plan-level checks are not sufficient.
