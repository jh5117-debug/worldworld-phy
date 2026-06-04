# Final Report: Non-Drop Upstream Fix and Template-Diverse TDW Smoke

Date: 2026-06-04

## Root Cause

The non-drop templates did write HDF5, but the v2 wrapper passed a relative `--dir local_assets/...` while running the upstream subprocess from the upstream Physion workspace. Files landed under:

`/home/nvme03/workspace/physion_moving_camera_mainline_20260505/local_assets/...`

instead of the project `local_assets` tree.

The fix resolves per-trial output directories to absolute paths and creates them before subprocess launch. Non-drop templates also keep upstream-style template-specific args and `--run 1`.

## Non-Drop 3-Sample

| Template | Result |
|---|---|
| `collision` | HDF5 ok, validation ok |
| `roll` | HDF5 ok, validation ok |
| `containment` | HDF5 ok, validation ok |

Validation: 3/3 OK, 3/3 suitable for warmup.

## Template-Diverse 10

| Template | Planned | Actual OK |
|---|---:|---:|
| `drop` | 3 | 3 |
| `collision` | 3 | 3 |
| `roll` | 2 | 2 |
| `containment` | 2 | 2 |

Validation:

- HDF5: 10/10
- RGB/depth/ID/camera/object state: 10/10
- `target_visible_ratio`: 1.0 for all
- max invisible frames: 0 for all
- suitable for warmup: 10/10

Conversion:

- LingBot cam-only samples: 10/10
- target.mp4 probe: 10/10
- `use_action=false`: 10/10
- dummy action zero norm: 10/10

## 50 Readiness

50-sample validation is ready only as an approval request. It was not run.

Approval request:

`docs/gpu_usage_approval_request_tdw_template_diverse_50.md`

## Safety

- no training
- no DPO
- no VideoGPA `03_train.py`
- no Stage1
- no LoRA/checkpoint saved
- no 50/200/1k generation
- no `local_assets` pushed

## Next Actions

1. User may approve GPU0-bound `DISPLAY=:8` for template-diverse 50-sample validation, or configure GPU6/7 display first.
2. DPO signal remains a separate no-go gate.
3. Full TDW generation only after staged validation and explicit approval.

