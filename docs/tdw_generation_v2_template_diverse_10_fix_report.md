# TDW Generation v2 Template-Diverse 10 Fix Report

Date: 2026-06-04

## Setup

Manifest:

`local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_10_fix.jsonl`

Approved display:

`DISPLAY=:8` GPU0-bound TDW/Unity display, approved only for this 10-sample smoke after non-drop 3/3 passed.

## Planned Distribution

| Template | Count |
|---|---:|
| `drop` | 3 |
| `collision` | 3 |
| `roll` | 2 |
| `containment` | 2 |

No stress/reobserve camera variants were present.

## Actual Generation

| Template | Count | Return code | HDF5 validation |
|---|---:|---:|---|
| `drop` | 3 | 0/0/0 | 3/3 ok |
| `collision` | 3 | 0/0/0 | 3/3 ok |
| `roll` | 2 | 0/0 | 2/2 ok |
| `containment` | 2 | 0/0 | 2/2 ok |

Validation summary:

- Generated HDF5 count: 10
- Validation OK count: 10
- Suitable for warmup count: 10
- Rejected count: 0
- `target_visible_ratio`: 1.0 for all samples
- max invisible frames: 0 for all samples
- RGB/depth/ID/camera/object-state completeness: 10/10

Camera path lengths ranged from mild dolly/strafe values around 0.10/0.25 to mild orbit values around 0.59.

## Gate

Template-diverse 10-sample warmup_mild smoke: passed.

No 50-sample generation was run.

