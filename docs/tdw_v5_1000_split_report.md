# TDW v5 1000 Split Report

Date: 2026-06-14

Split root:

`local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits/`

## Counts

- train: 800
- val: 100
- test: 100

## Template Distribution

Train:

- drop: 240
- collision: 240
- roll: 160
- containment: 160

Val:

- drop: 30
- collision: 30
- roll: 20
- containment: 20

Test:

- drop: 30
- collision: 30
- roll: 20
- containment: 20

## Camera Distribution

Train:

- orbit_left_72: 240
- orbit_right_60: 160
- orbit_left_44: 160
- orbit_right_64: 120
- strafe_left_180: 120

Val:

- orbit_left_72: 30
- orbit_right_60: 20
- orbit_left_44: 20
- orbit_right_64: 15
- strafe_left_180: 15

Test:

- orbit_left_72: 30
- orbit_right_60: 20
- orbit_left_44: 20
- orbit_right_64: 15
- strafe_left_180: 15

The split is balanced by template and camera_variant.

