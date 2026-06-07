# TDW v5 aggressive 2x demo validation

Generated HDF5: 5/5
Validation OK: 5/5
Suitable for warmup key/visibility gate: 5/5
Suitable for strict v5 visible motion: 2/5
Too static under v5 strict threshold: 3/5
Too extreme: 0/5
Delayed camera motion: 0/5
Unique scene hash: 5/5

Motion stats min / avg / max:
- camera_path_length: 1.8034 / 3.1506 / 3.6352
- camera_path_length_first_8_frames: 0.1803 / 0.3151 / 0.3635
- background_motion_proxy: 0.0252 / 0.0390 / 0.0506
- background_motion_proxy_first_8_frames: 0.0204 / 0.0299 / 0.0383
- target_visible_ratio: 1.0000 / 1.0000 / 1.0000

Interpretation:
- Geometric camera movement is much larger than v4/v3, with all samples moving from frame 0.
- Visibility is stable: all target_visible_ratio values are 1.0 and max invisible frames are 0 in the markdown validation table.
- Three samples fail the strict v5 `too_static` flag because the high background-motion threshold is not met, even though their camera path lengths are large. These are still converted for human visual review.

Raw validation markdown: `local_assets/data/physion/generated_v3/reports/validation_warmup_visible_motion_v5_aggressive_2x_demo_5.md`
Validation JSON: `local_assets/data/physion/generated_v3/reports/validation_warmup_visible_motion_v5_aggressive_2x_demo_5.json`

| idx | template | camera | path | first8 path | bg motion | bg first8 | visible | too_static | too_extreme | delayed | suitable | contact sheet |
|---:|---|---|---:|---:|---:|---:|---:|---|---|---|---|---|
| 0 | drop | orbit_left_72 | 3.5566 | 0.3557 | 0.0506 | 0.0336 | 1.0 | False | False | False | True | `local_assets/data/physion/generated_v3/reports/contact_sheets/00000_drop_orbit_left_72_seed22000_0000_contact_sheet.jpg` |
| 1 | collision | orbit_right_64 | 3.6352 | 0.3635 | 0.0321 | 0.0228 | 1.0 | True | False | False | False | `local_assets/data/physion/generated_v3/reports/contact_sheets/00001_collision_orbit_right_64_seed22001_0000_contact_sheet.jpg` |
| 2 | collision | strafe_left_180 | 1.8034 | 0.1803 | 0.0414 | 0.0383 | 1.0 | True | False | False | False | `local_assets/data/physion/generated_v3/reports/contact_sheets/00002_collision_strafe_left_180_seed22002_0000_contact_sheet.jpg` |
| 3 | roll | orbit_right_60 | 3.4982 | 0.3498 | 0.0252 | 0.0204 | 1.0 | True | False | False | False | `local_assets/data/physion/generated_v3/reports/contact_sheets/00003_roll_orbit_right_60_seed22003_0000_contact_sheet.jpg` |
| 4 | containment | orbit_left_44 | 3.2593 | 0.3259 | 0.0459 | 0.0341 | 1.0 | False | False | False | True | `local_assets/data/physion/generated_v3/reports/contact_sheets/00004_containment_orbit_left_44_seed22004_0000_contact_sheet.jpg` |
