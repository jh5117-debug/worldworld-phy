# Final Report: Non-Drop `--run 1` Retry and Template-Diverse Gate

Date: 2026-06-04

## 1. Non-Drop 3-Sample

Remote execution worktree:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_template_diverse_run_work`

Branch:

`physion-nondrop-run1-template-diverse`

Base commit:

`39095f66d1dce80b784708d7c7abf69616eec9d0`

`local_assets` remained a symlink to the shared project asset tree. No assets or weights were moved or deleted.

### Command Dry-Run

Passed.

| Template | `--run 1` | Drop-only args absent | Template in command/output dir | Camera variant |
|---|---|---|---|---|
| collision | yes | yes | yes | `orbit_left_12` |
| roll | yes | yes | yes | `orbit_right_12` |
| containment | yes | yes | yes | `strafe_left_025` |

Drop-only args checked:

- `--drop`
- `--ymin`
- `--ymax`
- `--dscale`

### Actual Result

The approved GPU0-bound `DISPLAY=:8` non-drop smoke ran in `tmux`.

| Template | Return code | HDF5 accepted | Validation |
|---|---:|---:|---|
| collision | 0 | 0 | failed; no HDF5 |
| roll | 0 | 0 | failed; no HDF5 |
| containment | 0 | 0 | failed; no HDF5 |

Validation report:

`local_assets/data/physion/generated_v2/reports/validation_nondrop_smoke_3_run1.md`

Accepted count: `0/3`.

The previous `--run 1` blocker is fixed. The current blocker is that upstream non-drop templates exit successfully but do not write HDF5 for this random single-sample wrapper invocation.

## 2. Template-Diverse 10

Not run.

The dependency condition required non-drop 3-sample validation to pass 3/3. It failed 0/3.

Planned distribution remains:

| Template | Count |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

Conversion was also skipped because there were no accepted template-diverse samples.

Video deliverables were not updated with new template-diverse samples.

## 3. Safety

| Restriction | Status |
|---|---|
| real training | not run |
| DPO training | not run |
| DPO signal sweep | not run |
| 5-pair | not run |
| VideoGPA `03_train.py` | not run |
| Stage1 | not run |
| LingBot rollout | not run |
| reward calibration | not run |
| LoRA save | not run |
| checkpoint save | not run |
| 50/200/1k TDW generation | not run |
| `local_assets` committed | no |
| generated HDF5/MP4/NPY/logs committed | no |

## 4. Next Actions

1. Fix upstream non-drop template invocation: identify required `collision`, `roll`, and `containment` parameters/stimulus settings so each writes HDF5.
2. After that fix, rerun only the non-drop 3-sample smoke.
3. Run template-diverse 10 only after non-drop validates 3/3.
4. Ask for 50-sample approval only after template-diverse 10 validates and converts.
5. Keep DPO signal as a separate no-go gate; do not run 5-pair or real training.

