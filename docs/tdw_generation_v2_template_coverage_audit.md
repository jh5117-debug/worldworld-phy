# TDW Generation v2 Template Coverage Audit

Date: 2026-06-03

## Problem

The approved 10-sample `warmup_mild` smoke passed validation and LingBot conversion, but all generated samples used the `drop` template. This means the generation gate was valid for HDF5/key/visibility checks, but not sufficient for template coverage.

Required coverage before 50-sample validation:

| Template | Target Count in 10-sample Plan |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

## Audit Findings

| Question | Finding |
|---|---|
| Does `plan_trials` contain template fields? | Yes, but it previously only cycled templates; it did not support exact `template_counts`. |
| Did the prior actual 10 use plan templates? | No. The smoke runner used the existing batch wrapper path, which effectively produced drop-only outputs. |
| Does `scripts/31_run_tdw_generation_v2_smoke.sh` pass a plan? | Not previously. It now supports `--plan`. |
| Did `run_tdw_trial` ignore per-trial templates? | The batch path did. It now has a plan-per-trial path that reads the manifest and emits one upstream command per row. |
| Does upstream support non-drop templates? | Yes. `tdw_physion_multi_template_moving_camera.py` supports `--template {drop,collision,roll,containment}`. |
| Is `roll` the correct upstream template name? | Yes, `roll` is directly accepted by the upstream script. |
| Is `containment` supported? | Yes, `containment` is directly accepted by the upstream script. |
| How is template forced now? | `run_tdw_trial --plan ...` calls the upstream multi-template script once per planned row with explicit `--template`. |
| How are output dirs named? | `raw_hdf5/warmup_mild_template_diverse_10samples/{index}_{template}_{camera_variant}_seed{seed}`. |
| How is metadata preserved? | The manifest contains `template`, `camera_variant`, `seed`, camera args, and filters. The runner report records per-trial commands and results. |

## Code Changes

- `cam_physgeo/data/tdw_generation_v2/plan_trials.py`
  - Added `--template_counts`.
  - Added exact template sequence validation.
  - Added `template_distribution` in the plan summary.

- `cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py`
  - Added `--plan`.
  - Added plan-per-trial execution mode.
  - Added per-template upstream command construction.
  - Added plan command logging.
  - Preserves GPU/display guard behavior.
  - Ignores only the obsolete batch-runner `main()` blocker in plan mode; GPU/display blockers still block actual execution.

- `scripts/31_run_tdw_generation_v2_smoke.sh`
  - Added `--plan` passthrough.

- `cam_physgeo/data/tdw_generation_v2/validate_generated_hdf5.py`
  - Added `--manifest` filtering so validation can target only the template-diverse run.

- `cam_physgeo/data/tdw_generation_v2/convert_generated_to_lingbot.py`
  - Added `--manifest` filtering so conversion can target only accepted template-diverse samples.

## Forced Command Shape

Each trial is now generated with a command shaped like:

```bash
python tdw_physion_multi_template_moving_camera.py \
  --template <drop|collision|roll|containment> \
  --dir <generated_v2/raw_hdf5/warmup_mild_template_diverse_10samples/...> \
  --num 1 \
  --camera_motion <orbit|strafe|dolly> \
  --camera_orbit_degrees <mild value> \
  --camera_strafe_distance <mild value> \
  --write_passes _img,_id,_depth
```

## Fix Status

The template coverage fix passed local dry-run validation. Actual TDW generation was not run because template-diverse 10 samples would require the GPU0-bound `DISPLAY=:8`, and this prompt did not grant that new GPU0 approval.

