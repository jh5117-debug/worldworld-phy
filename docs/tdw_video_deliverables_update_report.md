# TDW Video Deliverables Update Report

## Status

Partial update.

The new TDW v2 `warmup_mild` 1-sample HDF5 and contact sheet are available for
local review, but the generated LingBot `target.mp4` still needs a
probe-confirmed rewrite before it is added as a complete video deliverable.

## New TDW v2 Warmup Mild Sample

| Field | Value |
|---|---|
| Type | Physion-style TDW simulated clean GT |
| Profile | `warmup_mild` |
| Template | `drop` |
| Camera variant | `orbit_left_12` |
| HDF5 | `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_1samples/00000_drop_orbit_left_12_seed10000/0000.hdf5` |
| Contact sheet | `local_assets/data/physion/generated_v2/reports/contact_sheets/00000_drop_orbit_left_12_seed10000_0000_contact_sheet.jpg` |
| Target visible ratio | 1.0 |
| Max invisible frames | 0 |
| Camera path length | 0.5927 |
| Suitable for warmup | yes, from HDF5 validation |
| LingBot cam-only dir | `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00000_drop_orbit_left_12_seed10000_0000` |
| LingBot MP4 status | partial; file emitted but probe failed |

## Presentation Use

Use the contact sheet for the next mentor update. Do not present the LingBot
conversion MP4 until it is probe-confirmed.

## Existing Video Notes

- Old Physion-style TDW moving-camera samples remain useful as stress/test
  examples because some camera motion is too strong and foreground may leave
  frame.
- This new `warmup_mild` sample is the first staged v2 example with a mild
  camera variant and full target visibility.

No `local_assets` video/HDF5/contact-sheet files were added to Git.
