# GitHub Push Report: TDW v5 200 Stage A Balanced Warmup

Date: 2026-06-09

## Branch

`physion-tdw-v5-200-stageA-balanced-warmup`

## Remote

`ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Commit Message

`Add balanced Stage A warmup pilot with adapter checkpoint request`

## Scope Pushed

Code:

- `cam_physgeo/training/lingbot_warmup_smoke.py`

Docs:

- `docs/current_state_before_stageA_balanced_warmup.md`
- `docs/gpu_cleanup_before_stageA_balanced_warmup.md`
- `docs/stageA_balanced_sampler_audit_report.md`
- `docs/stageA_balanced_sampler_dryrun_report.md`
- `docs/experiment_registry_tdw_v5_200_stageA_balanced_warmup.md`
- `docs/tdw_v5_200_stageA_balanced_warmup_report.md`
- `docs/gpu_usage_approval_request_stageA_balanced_rollout_smoke.md`
- `docs/gpu_usage_approval_request_tdw_v5_200_stageB_or_rollout.md`
- `docs/final_report_tdw_v5_200_stageA_balanced_warmup.md`
- PRD and plan updates under `docs/`.

## Safety Check

Not committed:

- `local_assets/`;
- train metrics;
- adapter checkpoint;
- generated videos;
- HDF5 / MP4 / NPY / NPZ;
- optimizer state;
- full model weights;
- LoRA / safetensors / checkpoints under data or experiment folders;
- logs or large artifacts.

## Push Status

Initial push succeeded and set upstream tracking for:

`origin/physion-tdw-v5-200-stageA-balanced-warmup`

The branch contains code/docs only. Runtime artifacts remain local under `local_assets` and are intentionally excluded from Git.
