# TDW Generation v2 Non-Drop 3-Sample `--run 1` Report

Date: 2026-06-04

## Scope and Approval

The user approved GPU0-bound `DISPLAY=:8` for exactly:

- `collision`: 1 sample;
- `roll`: 1 sample;
- `containment`: 1 sample.

No template-diverse 10, 50/200/1k generation, DPO, VideoGPA `03_train.py`, Stage1, LoRA save, or checkpoint save was run unless this gate passed. It did not pass.

## Actual Command

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_nondrop_smoke_3_run1.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

The command was run in `tmux` session `tdw_nondrop_run1` to survive SSH resets.

Logs:

- outer log: `local_assets/data/physion/generated_v2/logs/nondrop_run1_outer.log`
- GPU before: `local_assets/data/physion/generated_v2/logs/nondrop_run1_gpu_before.txt`
- GPU after: `local_assets/data/physion/generated_v2/logs/nondrop_run1_gpu_after.txt`
- exit code: `local_assets/data/physion/generated_v2/logs/nondrop_run1_exit_code.txt`
- trial logs: `local_assets/data/physion/generated_v2/logs/run_warmup_mild_plan_3_trial_*.stdout_stderr.log`

## Command-Level Result

| Template | Camera variant | Return code | Run report HDF5 |
|---|---|---:|---|
| collision | `orbit_left_12` | 0 | `None` |
| roll | `orbit_right_12` | 0 | `None` |
| containment | `strafe_left_025` | 0 | `None` |

Run report:

`local_assets/data/physion/generated_v2/reports/run_warmup_mild_plan_3.json`

Wrapper status: `passed`, `failed_count=0`.

## Validation

```bash
python3 -m cam_physgeo.data.tdw_generation_v2.validate_generated_hdf5 \
  --root local_assets/data/physion/generated_v2 \
  --manifest local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_nondrop_smoke_3_run1.jsonl \
  --out local_assets/data/physion/generated_v2/reports/validation_nondrop_smoke_3_run1.md \
  --make_contact_sheet
```

Validation report:

`local_assets/data/physion/generated_v2/reports/validation_nondrop_smoke_3_run1.md`

| Template | Expected path | HDF5 exists / accepted | RGB/depth/id/camera/object state | target_visible_ratio | suitable_for_warmup | Failure reason |
|---|---|---|---|---:|---|---|
| collision | `.../00000_collision_orbit_left_12_seed22000/temp.hdf5` | no / no | not checked | n/a | no | no HDF5 written |
| roll | `.../00001_roll_orbit_right_12_seed22001/temp.hdf5` | no / no | not checked | n/a | no | no HDF5 written |
| containment | `.../00002_containment_strafe_left_025_seed22002/temp.hdf5` | no / no | not checked | n/a | no | no HDF5 written |

Validation summary:

| Metric | Value |
|---|---:|
| expected manifest rows | 3 |
| validation OK | 0 |
| suitable_for_warmup | 0 |
| accepted HDF5 | 0 |

## Log Observation

Each upstream trial printed TDW startup information, `SET RANDOM SEED`, and `tdw closed successfully`, but completed the single-trial loop immediately and wrote no HDF5.

The `--run 1` flag is present, so the previous execution-flag blocker is fixed. The current blocker is upstream non-drop template generation producing no HDF5 under this random single-sample invocation.

## Gate Decision

Non-drop 3-sample with `--run 1`: **failed**.

Because this gate was not 3/3 validation OK, template-diverse 10 was **not run**.

