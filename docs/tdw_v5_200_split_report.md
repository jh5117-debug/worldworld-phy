# TDW v5 200 Split Report

Date: 2026-06-09

## Inputs

- Manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_lingbot_manifest.jsonl`
- Split root: `local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/`
- Seed: 42
- Balance keys: `template,camera_variant`

## Counts

- Train: 160
- Val: 20
- Test: 20

## Train Distribution

- Templates: collision 48, containment 32, drop 48, roll 32
- Camera variants:
  - `orbit_right_64`: 24
  - `strafe_left_180`: 24
  - `orbit_left_44`: 32
  - `orbit_left_72`: 48
  - `orbit_right_60`: 32
- Unique scene hashes: 160

## Val Distribution

- Templates: collision 6, containment 4, drop 6, roll 4
- Camera variants:
  - `orbit_right_64`: 3
  - `strafe_left_180`: 3
  - `orbit_left_44`: 4
  - `orbit_left_72`: 6
  - `orbit_right_60`: 4
- Unique scene hashes: 20

## Test Distribution

- Templates: collision 6, containment 4, drop 6, roll 4
- Camera variants:
  - `orbit_right_64`: 3
  - `strafe_left_180`: 3
  - `orbit_left_44`: 4
  - `orbit_left_72`: 6
  - `orbit_right_60`: 4
- Unique scene hashes: 20

## Leakage Check

- Train/val scene overlap: 0
- Train/test scene overlap: 0
- Val/test scene overlap: 0

The split is ready for dataloader smoke.
