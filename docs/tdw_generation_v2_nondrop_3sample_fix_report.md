# TDW Generation v2 Non-Drop 3-Sample Fix Report

Date: 2026-06-04

## Setup

Approved display: `DISPLAY=:8`  
Detected use: GPU0-bound TDW/Unity display  
Scope: exactly three non-drop samples

Manifest:

`local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_nondrop_smoke_3_fix.jsonl`

## Result

| Template | Camera variant | Return code | HDF5 | Validation | Visible ratio | Max invisible | Camera path |
|---|---|---:|---|---|---:|---:|---:|
| `collision` | `orbit_left_12` | 0 | present | ok | 1.0 | 0 | 0.6815 |
| `roll` | `orbit_right_12` | 0 | present | ok | 1.0 | 0 | 0.7373 |
| `containment` | `strafe_left_025` | 0 | present | ok | 1.0 | 0 | 0.2508 |

Validation summary:

- HDF5 count: 3
- Validation OK: 3
- Suitable for warmup: 3
- RGB/depth/ID: present for all
- camera pose / position / aim: present for all
- projection/camera matrix: present for all
- object state: present for all

Contact sheets:

- `local_assets/data/physion/generated_v2/reports/contact_sheets/00000_collision_orbit_left_12_seed22000_0000_contact_sheet.jpg`
- `local_assets/data/physion/generated_v2/reports/contact_sheets/00001_roll_orbit_right_12_seed22001_0000_contact_sheet.jpg`
- `local_assets/data/physion/generated_v2/reports/contact_sheets/00002_containment_strafe_left_025_seed22002_0000_contact_sheet.jpg`

## Gate

Non-drop template smoke: passed.

Template-diverse 10 was allowed after this gate passed.

