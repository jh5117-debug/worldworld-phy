# TDW Generation v2 visible-motion v2 50 Actual Report

Approval:

- User approved GPU0-bound `DISPLAY=:8` for this 50-sample validation only.
- No 200 / 1k generation was run.

## Generation

- Generated HDF5: 50/50
- Failed commands: 0
- Display: `:8`
- GPU: GPU0
- GPU before: 28 MiB, 0% utilization
- GPU after: 28 MiB, 0% utilization
- Disk before: `/home/nvme04` about 953 GB free
- Disk after: `/home/nvme04` about 949 GB free
- Approximate generation runtime from polling: about 1h45m
- Raw HDF5 bytes: 4,307,788,467 bytes

## Validation

- Validation OK: 50/50
- Accepted / suitable for visible motion: 50/50
- Rejected: 0/50
- Acceptance rate: 100%
- `too_static`: 0
- `too_extreme`: 0

Planned and actual template distribution:

| Template | Planned | Accepted | Rejected |
|---|---:|---:|---:|
| drop | 15 | 15 | 0 |
| collision | 15 | 15 | 0 |
| roll | 10 | 10 | 0 |
| containment | 10 | 10 | 0 |

Camera distribution:

| Camera variant | Count |
|---|---:|
| orbit_left_24 | 10 |
| orbit_right_24 | 9 |
| strafe_left_050 | 8 |
| strafe_right_050 | 8 |
| orbit_left_28 | 4 |
| orbit_right_28 | 3 |
| orbit_left_18 | 2 |
| orbit_right_18 | 2 |
| orbit_left_20 | 2 |
| orbit_right_20 | 2 |

Motion metrics:

| Metric | Min | Avg | Max |
|---|---:|---:|---:|
| camera_path_length | 0.5016 | 1.0778 | 1.4814 |
| yaw_change_proxy | 6.7214 | 18.7175 | 28.0000 |
| background_motion_proxy | 0.0121 | 0.0211 | 0.0332 |
| parallax_proxy | 0.0121 | 0.0211 | 0.0332 |

`translation_magnitude` is not emitted by the current validator as a separate field. Translation is currently covered by `camera_path_length`.

Visibility:

- target_visible_ratio min/avg/max: 1.0 / 1.0 / 1.0
- max invisible frames avg/max: 0 / 0
- target_area_ratio_avg: not emitted by the current validator

Representative contact sheets:

- `local_assets/data/physion/generated_v2/reports/contact_sheets/00000_drop_orbit_left_24_seed22000_0000_contact_sheet.jpg`
- `local_assets/data/physion/generated_v2/reports/contact_sheets/00015_collision_strafe_left_050_seed22015_0000_contact_sheet.jpg`
- `local_assets/data/physion/generated_v2/reports/contact_sheets/00030_roll_strafe_left_050_seed22030_0000_contact_sheet.jpg`
- `local_assets/data/physion/generated_v2/reports/contact_sheets/00040_containment_orbit_left_18_seed22040_0000_contact_sheet.jpg`

Comparison:

- v2 10 accepted: 10/10
- v2 50 accepted: 50/50
- old `warmup_mild` 50 remains pipeline-valid but motion-too-weak.

