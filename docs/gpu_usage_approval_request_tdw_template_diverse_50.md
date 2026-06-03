# GPU Usage Approval Request: TDW Template-Diverse 50-Sample Validation

Date: 2026-06-03

## Status

Not ready.

The template-diverse 10-sample actual run has not yet been approved or executed. Therefore 50-sample validation must not run.

## Current Requirements Before 50

| Requirement | Status |
|---|---|
| Template-diverse plan | passed |
| Template-diverse 10 actual | pending GPU0 approval |
| Template-diverse 10 validation | not run |
| Template-diverse LingBot conversion | not run |
| Accepted ratio known | no |
| GPU0 approval for 50 | not granted |

## 50-Sample Command Placeholder

Only after template-diverse 10 passes and the user approves GPU0 or a GPU6/7 display is configured:

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

This placeholder must be replaced with a template-diverse manifest-based 50 plan before execution.

## Recommendation

Do not approve 50 until:

1. template-diverse 10 actual passes;
2. per-template validation is clean;
3. LingBot conversion probes pass;
4. storage/time estimate is updated from actual template-diverse results.

