# TDW v2 50-Sample Motion Quality Reassessment

Date: 2026-06-05

## Conclusion

The existing template-diverse 50-sample TDW v2 batch passed pipeline validation, but it should not be treated as final warmup main data for a camera-conditioned world model.

It is now reclassified as:

`template-diverse 50 pipeline validation passed`

not:

`warmup data quality passed`

## What Passed

- HDF5 generated: 50/50
- HDF5 validation: 50/50
- LingBot cam-only conversion: 50/50
- target.mp4 probe: 50/50
- `use_action=false`: 50/50
- dummy zero `action.npy`: 50/50
- template distribution: `drop:15`, `collision:15`, `roll:10`, `containment:10`

## Why It Is Not Final Warmup Data

The camera motion is too weak visually:

- `orbit_left_12` / `orbit_right_12` are only 12-degree orbits.
- `strafe_left_025` / `strafe_right_025` are only 0.25 scene units.
- `dolly_in_010` / `dolly_out_010` are only 0.10 scene units and are nearly invisible in contact sheets.

Observed camera path lengths from the validation report:

- minimum: `0.1005`
- average: `0.3682`
- maximum: `0.8888`

Many clips therefore look close to ordinary I2V generation instead of clearly camera-conditioned prediction. The current validator accepted them because it checked schema, visibility, and object/camera metadata, but did not require visible camera movement or parallax.

## Required Fix

Add a new profile:

`warmup_visible_motion`

This profile should be stronger than `warmup_mild`, but must remain non-stress:

- no lookaway;
- no offscreen;
- no reobserve;
- no `relative_yaw_180`;
- no long foreground disappearance.

Old 50-sample data should be preserved for pipeline and conversion regression tests. Do not delete, overwrite, or treat it as final warmup main data.
