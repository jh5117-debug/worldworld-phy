# TDW Generation v2 Non-Drop 3-Sample Actual Report

Date: 2026-06-04

## Approval and Scope

The user approved GPU0-bound `DISPLAY=:8` for one non-drop per-template smoke:

- `collision`: 1 sample;
- `roll`: 1 sample;
- `containment`: 1 sample.

No 10-sample retry, 50-sample validation, 200/1k generation, training, DPO training, LoRA save, or checkpoint save was run from this gate.

## Actual Command

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_nondrop_smoke_3.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

## Command-Level Outcome

| Template | Command return | Expected HDF5 |
|---|---:|---|
| collision | 0 | `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_plan_3samples/00000_collision_orbit_left_12_seed22000/temp.hdf5` |
| roll | 0 | `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_plan_3samples/00001_roll_orbit_right_12_seed22001/temp.hdf5` |
| containment | 0 | `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_plan_3samples/00002_containment_strafe_left_025_seed22002/temp.hdf5` |

Outer run log:

`local_assets/data/physion/generated_v2/logs/nondrop_smoke_3_outer.log`

Run report:

`local_assets/data/physion/generated_v2/reports/run_warmup_mild_plan_3.json`

## Validation Outcome

Validation command:

```bash
python -m cam_physgeo.data.tdw_generation_v2.validate_generated_hdf5 \
  --root local_assets/data/physion/generated_v2 \
  --manifest local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_nondrop_smoke_3.jsonl \
  --out local_assets/data/physion/generated_v2/reports/validation_nondrop_smoke_3.md \
  --make_contact_sheet
```

| Template | HDF5 exists | RGB/depth/id/camera/object state | target_visible_ratio | suitable_for_warmup | Failure reason |
|---|---|---|---:|---|---|
| collision | no | not checked | n/a | no | no HDF5 produced |
| roll | no | not checked | n/a | no | no HDF5 produced |
| containment | no | not checked | n/a | no | no HDF5 produced |

Validation accepted count: `0/3`.

## Exact Blocker

The command builder had correctly removed drop-only arguments from non-drop templates, but it was still missing the upstream execution flag:

```text
--run 1
```

The upstream runner `tdw_physion_multi_template_moving_camera.py` only executes generation inside `if bool(args.run):`. Without `--run 1`, the wrapper can return successfully while producing no HDF5.

## Fix Applied

`cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py` now adds:

```text
--run 1
```

to each upstream command.

## Gate Decision

TDW non-drop 3-sample actual: **failed validation / blocker fixed in wrapper**.

Because the non-drop validation did not pass, the dependency rule blocked template-diverse 10 retry in this turn. A fresh user approval is required before rerunning actual TDW generation with the fixed `--run 1` command.

