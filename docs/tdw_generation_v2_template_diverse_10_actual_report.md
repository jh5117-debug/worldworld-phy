# TDW Generation v2 Template-Diverse 10 Actual Report

Date: 2026-06-04

## Approval

The user explicitly approved GPU0-bound `DISPLAY=:8` for exactly one 10-sample template-diverse `warmup_mild` TDW smoke.

No 50/200/1k generation was run.

## Setup

| Item | Value |
|---|---|
| Worktree | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_template_diverse_run_work` |
| Branch | `physion-template-diverse-tdw-dpo-signal-run` |
| Base commit | `22b887c` |
| local_assets | symlink to the main shared asset tree |
| Display | `:8` |
| GPU | GPU0-bound TDW/Unity display |
| Profile | `warmup_mild` |
| Manifest | `local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_10.jsonl` |

## Planned Distribution

| Template | Planned Count |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

Stress/reobserve bad count: `0`.

## Actual Result

| Template | Planned | Command Return Status |
|---|---:|---|
| drop | 3 | 3 commands returned 0 |
| collision | 3 | 3 commands failed with return code 2 |
| roll | 2 | 2 commands failed with return code 2 |
| containment | 2 | 2 commands failed with return code 2 |

Overall run report:

| Item | Value |
|---|---|
| Run report | `local_assets/data/physion/generated_v2/reports/run_warmup_mild_plan_10.json` |
| Status | failed |
| Return code | 1 |
| Failed count | 7 |
| Validation report | `local_assets/data/physion/generated_v2/reports/validation_template_diverse_10.md` |
| Validation accepted count | 0 |
| Suitable for warmup | 0 |

## Exact Blocker

The non-drop templates failed because the first plan-mode command builder passed drop-specific arguments to every template:

- `--drop`
- `--ymin`
- `--ymax`
- `--dscale`

The upstream `tdw_physion_multi_template_moving_camera.py` parser rejects these arguments for `collision`, `roll`, and `containment`, so those seven trials exited before generation.

The three `drop` trials returned successfully, but manifest validation found no accepted final HDF5 paths for this template-diverse run. Therefore this batch is not usable for warmup.

## Fix Applied

`cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py` now only appends the drop-specific arguments when `template == "drop"`.

Local dry-run check after the fix:

| Template | Drop-Specific Args Present |
|---|---|
| drop | yes |
| collision | no |
| roll | no |
| containment | no |

No second GPU0 actual generation was run in this turn because the user approved exactly one 10-sample attempt.

## Gate Decision

TDW template-diverse actual 10-sample gate: **failed / blocked with exact upstream-argument issue**.

Next action: approve one more GPU0 `DISPLAY=:8` template-diverse 10-sample smoke after this command fix, or configure TDW on GPU6/7.

