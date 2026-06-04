# GPU Usage Approval Request: TDW Template-Diverse 50-Sample Validation

Date: 2026-06-04

## Current Status

Template-diverse 10-sample `warmup_mild` smoke passed:

- planned distribution: drop 3 / collision 3 / roll 2 / containment 2
- generated HDF5: 10
- validation OK: 10
- suitable for warmup: 10
- rejected: 0
- LingBot cam-only conversion: 10
- target.mp4 probe: 10
- `use_action=false`: 10
- dummy action zero norm: 10

## Requested Next Stage

Run template-diverse 50-sample TDW validation on the same staged pipeline.

This requires explicit user approval because TDW currently uses GPU0-bound `DISPLAY=:8`.

## Proposed Command

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --num_trials 50 \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

Validation and conversion would run only after generation completes.

## Risk / Estimate

The 10-sample run completed successfully, but 50 samples will take longer and will continue using GPU0-bound TDW/Unity display. It should not be started without explicit approval.

Alternatives:

1. Configure a GPU6/7 TDW display first.
2. Pause TDW generation and continue DPO signal debugging.
3. Run a smaller additional template balance smoke instead of 50.

## Recommendation

50-sample validation is technically ready after this 10-sample pass, but requires user approval before execution.

