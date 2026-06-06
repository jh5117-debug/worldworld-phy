# TDW v3 start0 scene-diverse 50 validation report

Profile: `warmup_visible_motion_v3_start0_scene_diverse`

Result: generation and HDF5/key validation succeeded, but the dataset is **not ready for warmup main data** because the visible-motion acceptance target failed.

| Metric | Value |
|---|---:|
| Generated HDF5 | 50 / 50 |
| Validation OK | 50 / 50 |
| Accepted for visible-motion v3 | 28 / 50 |
| Rejected | 22 / 50 |
| Acceptance rate | 56% |
| Too static | 22 |
| Too extreme | 0 |
| Delayed camera motion | 22 |
| Unique scene hashes | 50 / 50 |
| Duplicate scene hashes | 0 |

Planned and actual template distribution:

- drop: 15
- collision: 15
- roll: 10
- containment: 10

Accepted per template:

- drop: 11 / 15
- collision: 7 / 15
- roll: 4 / 10
- containment: 6 / 10

Camera result:

- Accepted cameras were all orbit variants: `orbit_left/right_20`, `orbit_left/right_22`, `orbit_left/right_26`, `orbit_left/right_28`, `orbit_left/right_32`, `orbit_left/right_36`.
- Rejected cameras were all strafe variants: `strafe_left/right_055` and `strafe_left/right_065`.

Motion metrics:

- camera_path_length_total min/avg/max: `0.5518 / 1.1758 / 1.7782`
- camera_path_length_first_8_frames min/avg/max: `0.0552 / 0.1176 / 0.1778`
- background_motion_proxy_total min/avg/max: `0.0209 / 0.0343 / 0.0539`
- background_motion_proxy_first_8_frames min/avg/max: `0.0132 / 0.0257 / 0.0512`
- target_visible_ratio min/avg/max: `1.0 / 1.0 / 1.0`
- max invisible frames: `0`

Interpretation:

- Scene diversity was fixed by v3: unique scene hash count reached `50/50`.
- Start0/orbit motion is effective: all orbit variants passed early-motion and total-motion gates.
- Strafe values are still too weak for the current total-path and early-path thresholds: all 22 strafe samples were rejected as `too_static` and `delayed_camera_motion`.

Validation report path:

`local_assets/data/physion/generated_v3/reports/validation_warmup_visible_motion_v3_start0_scene_diverse_50.md`

Contact sheet gallery:

`local_assets/data/physion/generated_v3/reports/contact_sheets/`

Conclusion: v3 is a useful diagnostic review set, but it is **not ready for 200** and should not be used as final warmup main data without tuning.
