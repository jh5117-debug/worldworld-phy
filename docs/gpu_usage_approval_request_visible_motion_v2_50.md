# GPU Usage Approval Request: warmup_visible_motion_v2 50-Sample Validation

## Current 10-Sample Result

`warmup_visible_motion_v2` 10-sample smoke passed:

- Generated HDF5: 10/10
- Validation OK: 10/10
- Suitable for visible motion: 10/10
- Converted to LingBot cam-only: 10/10
- Per-template accepted: drop 3, collision 3, roll 2, containment 2
- `too_static`: 0
- `too_extreme`: 0

This meets the readiness condition for a user-approved 50-sample validation request.

## Requested Task

Run a 50-sample `warmup_visible_motion_v2` validation batch.

Expected distribution:

- drop: 15
- collision: 15
- roll: 10
- containment: 10

## GPU Requirement

Current available TDW display for this workflow is GPU0-bound `DISPLAY=:8`. Running 50 samples would use GPU0 unless a GPU6/7 display is configured first.

## Command Requiring Approval

```bash
python3 -m cam_physgeo.data.tdw_generation_v2.plan_trials \
  --config configs/cam_physgeo/tdw_generation_v2.yaml \
  --profile warmup_visible_motion_v2 \
  --templates drop collision roll containment \
  --template_counts drop:15,collision:15,roll:10,containment:10 \
  --num_trials 50 \
  --out local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_v2_50.jsonl \
  --dry-run

bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_visible_motion_v2 \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_v2_50.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

## Recommendation

Approve the 50-sample validation only if GPU0 remains available for this TDW job. Do not proceed to 200 / 1k without another staged validation and explicit user approval.

