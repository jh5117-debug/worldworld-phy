# Full TDW Generation Readiness Report

## Decision

Not ready for full TDW generation.

## Current TDW Status

| Gate | Status |
|---|---|
| warmup_mild plan | passed |
| stress/reobserve filter | passed |
| 1-sample actual generation | passed |
| 1-sample HDF5 validation | passed |
| 1-sample LingBot conversion | partial |
| 10-sample smoke | not run |
| 50-sample validation | not run |
| 200 / 1k+ generation | not allowed |

## Why Full Generation Is Not Ready

- Only one TDW v2 `warmup_mild` sample has been generated.
- The HDF5 is complete and suitable for warmup, but LingBot target MP4 probe
  still needs a final writer/probe fix.
- No 10-sample smoke has validated template/camera diversity.
- No 50-sample validation has measured rejection rate, storage, and speed.
- The only confirmed TDW display is GPU0-bound `DISPLAY=:8`; multi-sample GPU0
  use requires explicit user approval.

## User Approval Needed Before More TDW Generation

For 10-sample smoke on the current display:

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --num_trials 10 \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allowed_gpu_ids 6,7 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

This would use the GPU0-bound display and should not be run without explicit
approval.

## DPO Interaction

DPO engineering gates are mostly complete, but signal-sensitivity remains weak
or incomplete. Full TDW generation can proceed later as a staged data source for
camera warmup and reward/DPO pools, but it should not be conflated with real DPO
training.

## Next Minimal Action

1. Finish probe-confirmed `target.mp4` writing for the accepted 1-sample.
2. Ask for explicit approval before GPU0 10-sample smoke, or configure a GPU6/7
   TDW display.
3. Run 10-sample, then 50-sample, then 200 pilot, each with validation.
4. Do not run 1k+ until staged validation and storage/time checks pass.
