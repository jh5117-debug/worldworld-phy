# TDW v5 200 Manifest / Split Recheck

Date: 2026-06-09

## Counts

| Split | Count |
|---|---:|
| all | 200 |
| train | 160 |
| val | 20 |
| test | 20 |

## Template Distribution

| Split | drop | collision | roll | containment |
|---|---:|---:|---:|---:|
| all | 60 | 60 | 40 | 40 |
| train | 48 | 48 | 32 | 32 |
| val | 6 | 6 | 4 | 4 |
| test | 6 | 6 | 4 | 4 |

## Camera Distribution

Top camera variants in the full manifest:

- `orbit_left_72`: 60
- `orbit_right_60`: 40
- `orbit_left_44`: 40
- `orbit_right_64`: 30
- `strafe_left_180`: 30

First-five path checks for each split found no missing `sample_dir`, `image_path`, `target_video_path`, `poses_path`, `intrinsics_path`, `action_path`, `prompt_path`, or `metadata_path`.

Ready for true model smoke: yes.
