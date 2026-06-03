# TDW Generation v2 GPU0 1-Sample Approval Report

## Approval Scope

The user explicitly approved using the current GPU0-bound `DISPLAY=:8` for exactly one `warmup_mild` TDW generation smoke. This approval does not allow 10-sample, 50-sample, training, DPO, Stage1, LingBot rollout, reward calibration, or any large generation.

## Preflight

- `warmup_mild` plan was checked before launch.
- `bad_count`: 0
- Stress/reobserve terms were absent from the plan.
- `DISPLAY`: `:8`
- Display GPU: GPU0
- GPU0 approval token used: `USER_CONFIRMED_UNAPPROVED_GPU`

## Run Attempts

No TDW/Unity sample completed. Both failures happened before a TDW scene was generated.

### Attempt 1

- status: failed before TDW/Unity launch
- return code: 2
- blocker: runtime wrapper path was relative while subprocess cwd was the upstream TDW workspace
- generated HDF5/MP4: none

Fix applied:

- `run_tdw_trial.py` now resolves the output root and runtime wrapper path to absolute paths before launching the upstream runner.

### Attempt 2

- status: failed before TDW/Unity launch
- return code: 1
- blocker: generated Python wrapper embedded JSON boolean `false` directly in Python source
- generated HDF5/MP4: none

Fix applied:

- runtime wrapper now assigns `MILD_CAMERA_VARIANTS = json.loads('<json text>')`, so JSON booleans are parsed correctly.

## GPU Usage

GPU readings after failed attempts showed GPU0 back at idle/minimal memory. No persistent TDW/Unity process was found.

## Result

No sample was generated in this run. The run stopped after the one approved 1-sample smoke path exposed wrapper startup blockers. No 10/50 generation was attempted.

