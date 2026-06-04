# TDW Generation v2 Template-Diverse 50 Plan Report

Date: 2026-06-05

## Scope

User approved GPU0-bound `DISPLAY=:8` for exactly one TDW / Physion-style generation v2 `warmup_mild` template-diverse 50-sample validation.

No 200/1k generation, training, DPO, VideoGPA `03_train.py`, Stage1, LingBot rollout, or reward calibration was allowed.

## Plan

Manifest:

`local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_50.jsonl`

Planned count: 50

| Template | Planned count |
|---|---:|
| `drop` | 15 |
| `collision` | 15 |
| `roll` | 10 |
| `containment` | 10 |

Camera variant distribution:

| Camera variant | Count |
|---|---:|
| `orbit_left_12` | 9 |
| `orbit_right_12` | 9 |
| `strafe_left_025` | 8 |
| `strafe_right_025` | 8 |
| `dolly_in_010` | 8 |
| `dolly_out_010` | 8 |

Stress/reobserve check:

- `lookaway`: 0
- `offscreen`: 0
- `relative_yaw_180`: 0
- `reobserve`: 0
- `extreme`: 0
- `occluder`: 0

`bad_count=0`.

## Estimate

Based on the successful 10-sample smoke, the expected 50-sample output was approximately:

- raw HDF5: several GiB;
- LingBot cam-only conversion: around 10 GiB;
- runtime: around 1.5-2 hours for generation plus validation/conversion.

