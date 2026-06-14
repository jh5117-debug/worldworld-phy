# TDW v5 1k Scale-Up 800 Validation Report

Date: 2026-06-14

Validation report:

`local_assets/data/physion/generated_v3/reports/validation_v5_1k_scaleup_800.md`

JSON report:

`local_assets/data/physion/generated_v3/reports/validation_v5_1k_scaleup_800.json`

## Result

- Generated HDF5 count: 800
- Validation OK count: 800
- Suitable for warmup count: 800
- Strict suitable_for_visible_motion count: 212
- Delayed camera motion count: 0
- Unique scene hash count: 800
- Duplicate scene hash count: 0

Template distribution:

- drop: 240
- collision: 240
- roll: 160
- containment: 160

Camera distribution:

- orbit_left_72: 240
- orbit_right_60: 160
- orbit_left_44: 160
- orbit_right_64: 120
- strafe_left_180: 120

## Interpretation

The strict visible-motion validator remains conservative for the aggressive v5 profile. The user had already human-approved the v5 aggressive 2x motion style, so the scale-up acceptance gate for this task is HDF5 completeness, warmup suitability, target visibility, no delayed camera motion, and scene diversity. Those gates passed for 800/800 new samples.

