# Final Report: Non-Drop TDW Template Retry and DPO Signal Gate

Date: 2026-06-04

## 1. TDW Non-Drop

Worktree used for remote execution:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_template_diverse_run_work`

Branch at execution time:

`physion-nondrop-template-retry-dpo-signal`

`local_assets` remained a symlink to the shared data/weights tree. No assets, videos, HDF5, NPY, latents, or weights were moved or deleted.

### Command Dry-Run

The non-drop command dry-run passed for:

| Template | Drop-only args present? | Output dir includes template? |
|---|---|---|
| collision | no | yes |
| roll | no | yes |
| containment | no | yes |

This confirms the previous blocker is fixed: `--drop`, `--ymin`, `--ymax`, and `--dscale` are no longer passed to non-drop templates.

### Actual Per-Template Smoke

The user-approved GPU0-bound `DISPLAY=:8` non-drop smoke ran:

| Template | Planned | Command return | Validation |
|---|---:|---:|---|
| collision | 1 | 0 | failed: no HDF5 |
| roll | 1 | 0 | failed: no HDF5 |
| containment | 1 | 0 | failed: no HDF5 |

Validation accepted count: `0/3`.

The exact new blocker is a missing upstream execution flag. The upstream runner only writes HDF5 when `--run 1` is set. The wrapper has now been fixed to include `--run 1` in all actual upstream TDW commands.

## 2. Template-Diverse Retry

The template-diverse 10 retry was **not run**.

Reason: the dependency gate required all three non-drop template smokes to validate. They did not validate because no HDF5 files were written.

Planned distribution remains:

| Template | Count |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

Next TDW action: request approval to rerun the fixed non-drop 3-sample smoke, then run the template-diverse 10 retry only if non-drop validation passes.

## 3. DPO Signal

Short `dpo_signal_sensitivity_fast` retry was launched on GPU6/7 only.

Settings:

| Item | Value |
|---|---|
| LR list | `1e-5`, `1e-4` |
| steps per LR | 3 |
| LoRA target | `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer` |
| rank / alpha | `2 / 4.0` |
| fixed noise seed | 123 |
| fixed timestep | 579 |

Result: the retry did not produce a usable two-LR summary in the safe runtime window. No 5-pair run was started.

DPO signal gate: **no-go**.

5-pair tiny overfit: **no-go**.

## 4. Safety

| Restriction | Status |
|---|---|
| real training | not run |
| VideoGPA `03_train.py` | not run |
| Stage1 | not run |
| LoRA save | not run |
| checkpoint save | not run |
| 50/200/1k TDW generation | not run |
| 5-pair tiny overfit | not run |
| local_assets committed | no |
| generated HDF5/MP4/NPY/logs committed | no |
| LingBot weights modified | no |

## 5. Next Actions

1. If continuing TDW: approve one fixed non-drop 3-sample rerun on `DISPLAY=:8`, or configure a GPU6/7 TDW display.
2. If non-drop validates after `--run 1`, run template-diverse 10 retry with the planned distribution.
3. Do not request or run 50 until template-diverse 10 passes validation and LingBot conversion.
4. For DPO, make the signal sweep faster or test a stronger camera-control LoRA target/scope.
5. Do not run 5-pair, 10-pair, VideoGPA `03_train.py`, Stage1, or real DPO training until the signal gate passes.

