# TDW Generation v2 Visible-Motion v2 10-Sample Actual Report

Date: 2026-06-05

## Status

Not run.

## Reason

The local `warmup_visible_motion_v2` code and dry-run plan passed, but the remote SSH control plane repeatedly timed out or reset while syncing code to the TDW helper worktree.

No v2 TDW actual generation was launched.

## Safety

- No v2 HDF5 was generated.
- No 50 / 200 / 1k was run.
- No training.
- No DPO.
- No VideoGPA `03_train`.
- No Stage1.
- No rollout or reward calibration.

## Next Exact Step

When SSH is stable, sync these files to the remote helper worktree:

- `configs/cam_physgeo/tdw_generation_v2.yaml`
- `cam_physgeo/data/tdw_generation_v2/generation_config.py`
- `cam_physgeo/data/tdw_generation_v2/plan_trials.py`
- `cam_physgeo/data/tdw_generation_v2/convert_generated_to_lingbot.py`

Then run:

```bash
python -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_visible_motion_v2 \
  --templates drop collision roll containment \
  --template_counts drop:3,collision:3,roll:2,containment:2 \
  --num_trials 10 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_v2_10.jsonl \
  --dry-run

bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_visible_motion_v2 \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_v2_10.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```
