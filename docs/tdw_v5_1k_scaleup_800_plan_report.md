# TDW v5 1k Scale-Up 800 Plan Report

Date: 2026-06-14

## Plan

Manifest:

`local_assets/data/physion/generated_v3/manifests/plan_warmup_visible_motion_v5_aggressive_2x_scaleup_800.jsonl`

Profile:

`warmup_visible_motion_v5_aggressive_2x_demo`

## Counts

- Planned rows: 800
- sample_index: 200-999
- seed range: 24000-24799
- output subdir: `warmup_visible_motion_v5_aggressive_2x_1k_scaleup_800samples`

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

Plan checks:

- No lookaway / offscreen / relative_yaw_180 / reobserve / occluder variants.
- Seeds are unique.
- Existing 200 data was not overwritten.

