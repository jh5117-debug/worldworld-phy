# Stage A Balanced Sampler Dry-Run Report

Date: 2026-06-09

Command ran on the TDW v5 200 train split without loading the model.

Manifest:

`local_assets/data/physion/generated_v3/manifests/tdw_v5_200_splits/train.jsonl`

Output:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/sampler_dryrun/`

## Result

Status: passed.

## Coverage

First 20:

| Template | Count |
|---|---:|
| drop | 5 |
| collision | 5 |
| roll | 5 |
| containment | 5 |

First 60:

| Template | Count |
|---|---:|
| drop | 15 |
| collision | 15 |
| roll | 15 |
| containment | 15 |

Camera variants in first 60:

- `orbit_left_72`: 15
- `strafe_left_180`: 8
- `orbit_right_60`: 15
- `orbit_left_44`: 15
- `orbit_right_64`: 7

Duplicate sample count: 0.

## Gate

Pass criteria:

- first 20 contains at least 3 templates: passed;
- first 60 contains all 4 templates: passed;
- first 60 contains at least 4 camera variants: passed;
- no excessive duplicates: passed.

Balanced Stage A training is allowed to proceed.
