# TDW Generation v2 Visible-Motion v2 10-Sample Actual Report

Approval: user approved GPU0-bound `DISPLAY=:8` for this v2 10-sample smoke only.

No 50 / 200 / 1k generation was run.

## Plan

| Template | Planned count |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

Camera variants:

- `orbit_left_24`: 2
- `orbit_right_24`: 1
- `orbit_left_28`: 1
- `strafe_left_050`: 2
- `strafe_right_050`: 2
- `orbit_left_18`: 1
- `orbit_right_18`: 1

The plan had `bad_count=0`, no stress/reobserve/offscreen/extreme variants, no roll dolly variants, and no containment orbit 24 / orbit 28 variants.

## Generation

- Generated HDF5: 10/10
- Failed commands: 0
- Display: `:8`
- GPU: GPU0, explicitly approved for this run
- GPU before generation: GPU0 28 MiB, 0% utilization
- GPU after generation: GPU0 28 MiB, 0% utilization
- Raw HDF5 directory: `local_assets/data/physion/generated_v2/raw_hdf5/warmup_visible_motion_v2_plan_10samples/`

## Validation

- Validation OK: 10/10
- Suitable for warmup: 10/10
- Suitable for visible motion: 10/10
- Rejected: 0/10
- `too_static`: 0/10
- `too_extreme`: 0/10
- Target visible ratio: min/avg/max = 1.0 / 1.0 / 1.0
- Max invisible frames: 0 for all samples
- Camera path length: min/avg/max = 0.5016 / 0.9790 / 1.3831
- Background motion proxy: min/avg/max = 0.0120 / 0.0204 / 0.0295

Per-template accepted count:

| Template | Accepted |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

Representative contact sheets:

- `local_assets/data/physion/generated_v2/reports/contact_sheets/00000_drop_orbit_left_24_seed22000_0000_contact_sheet.jpg`
- `local_assets/data/physion/generated_v2/reports/contact_sheets/00003_collision_strafe_left_050_seed22003_0000_contact_sheet.jpg`
- `local_assets/data/physion/generated_v2/reports/contact_sheets/00006_roll_strafe_left_050_seed22006_0000_contact_sheet.jpg`
- `local_assets/data/physion/generated_v2/reports/contact_sheets/00008_containment_orbit_left_18_seed22008_0000_contact_sheet.jpg`

Comparison with v1:

- v1 accepted 5/10.
- v2 accepted 10/10.
- v2 fixed the template-specific failures seen in v1.

