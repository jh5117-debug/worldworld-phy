# TDW Generation v2 Template-Diverse 50 Validation Report

Date: 2026-06-05

## Generation

Approved display: GPU0-bound `DISPLAY=:8`

Manifest:

`local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_50.jsonl`

Output:

`local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_template_diverse_50samples/`

Generation result:

| Metric | Value |
|---|---:|
| planned samples | 50 |
| generated HDF5 | 50 |
| command failures | 0 |
| rejected during validation | 0 |
| generation status | passed |

Actual template distribution:

| Template | Count | Validation OK |
|---|---:|---:|
| `drop` | 15 | 15 |
| `collision` | 15 | 15 |
| `roll` | 10 | 10 |
| `containment` | 10 | 10 |

Camera variant distribution:

| Camera variant | Count |
|---|---:|
| `orbit_left_12` | 9 |
| `orbit_right_12` | 9 |
| `strafe_left_025` | 8 |
| `strafe_right_025` | 8 |
| `dolly_in_010` | 8 |
| `dolly_out_010` | 8 |

## Validation

Validation report:

`local_assets/data/physion/generated_v2/reports/validation_template_diverse_50.md`

Validation JSON:

`local_assets/data/physion/generated_v2/reports/validation_template_diverse_50.json`

| Check | Result |
|---|---:|
| HDF5 exists | 50/50 |
| RGB / `_img` | 50/50 |
| `_depth` | 50/50 |
| `_id` | 50/50 |
| camera pose | 50/50 |
| camera position | 50/50 |
| camera aim | 50/50 |
| projection / camera matrix | 50/50 |
| object state | 50/50 |
| suitable for warmup | 50/50 |

Visibility and motion:

| Metric | Min | Avg | Max |
|---|---:|---:|---:|
| `target_visible_ratio` | 1.0 | 1.0 | 1.0 |
| max invisible frames | 0 | 0.0 | 0 |
| camera path length | 0.1005 | 0.3682 | 0.8888 |

Contact sheets:

`local_assets/data/physion/generated_v2/reports/contact_sheets/`

## Storage / Runtime

| Item | Value |
|---|---:|
| raw HDF5 directory | about 4.0 GiB |
| LingBot converted directory | about 9.1 GiB |
| contact sheets | about 6.4 MiB |
| generation runtime | about 1 hour 48 minutes |
| validation runtime | about 6 minutes |

GPU after generation:

- GPU0 returned to idle.
- No 200/1k generation was started.

