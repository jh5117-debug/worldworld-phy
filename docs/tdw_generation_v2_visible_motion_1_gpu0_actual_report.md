# TDW Generation v2 Visible-Motion 1-Sample GPU0 Actual Report

Date: 2026-06-05

## Approval

The user explicitly approved `DISPLAY=:8` / GPU0 for this one-sample visible-motion smoke.

## Result

| Item | Value |
|---|---|
| Generation status | passed |
| Return code | 0 |
| Template | `drop` |
| Camera variant | `orbit_left_24` |
| HDF5 path | `local_assets/data/physion/generated_v2/raw_hdf5/warmup_visible_motion_plan_1samples/00000_drop_orbit_left_24_seed22000/0000.hdf5` |
| Frame count | 83 |
| RGB / depth / ID | present |
| Camera pose / position / aim | present |
| Projection / camera matrix | present |
| Object state | present |
| Target visible ratio | 1.0 |
| Max invisible frames | 0 |
| Camera path length | 1.1854358679765697 |
| Background motion proxy | 0.02952023684470491 |
| Too static | false |
| Too extreme | false |
| Suitable for visible motion | true |
| Contact sheet | `local_assets/data/physion/generated_v2/reports/contact_sheets/00000_drop_orbit_left_24_seed22000_0000_contact_sheet.jpg` |

## Decision

The one-sample gate passed, so the 10-sample `warmup_visible_motion` smoke was allowed.
