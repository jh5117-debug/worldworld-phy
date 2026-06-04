# GPU Usage Approval Request: TDW Template-Diverse 50-Sample Validation

Date: 2026-06-04

## Status

Not ready.

The template-diverse 10-sample actual run was approved and attempted, but it failed. Therefore 50-sample validation must not run.

## Current Requirements Before 50

| Requirement | Status |
|---|---|
| Template-diverse plan | passed |
| Template-diverse 10 actual | failed: 3 drop commands returned 0, 7 non-drop commands failed |
| Template-diverse 10 validation | ran; 0 accepted |
| Template-diverse LingBot conversion | skipped |
| Accepted ratio known | 0/10 |
| GPU0 approval for 50 | not granted |

## 50-Sample Command Placeholder

Only after a fixed template-diverse 10 passes and the user approves GPU0 or a GPU6/7 display is configured:

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_mild_template_diverse_50.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

The 50 manifest must be generated with explicit template counts before execution.

## Recommendation

Do not approve 50 until:

1. template-diverse 10 actual passes after the template-specific args fix;
2. per-template validation is clean;
3. LingBot conversion probes pass;
4. storage/time estimate is updated from actual template-diverse results.

## 2026-06-04 Non-Drop Retry Update

50-sample validation is still **not ready**.

The approved non-drop per-template smoke (`collision:1`, `roll:1`, `containment:1`) returned successfully at the command level, but validation found no HDF5 files. The root cause was a missing upstream execution flag: the wrapper did not pass `--run 1`, and the upstream TDW runner only writes HDF5 when `args.run` is enabled.

The wrapper now adds `--run 1`, but no additional actual TDW generation was run because the approved smoke had already been consumed. Before any 50-sample approval, run the fixed non-drop 3-sample smoke again, then run and validate the template-diverse 10-sample retry.

## 2026-06-04 `--run 1` Retry Update

50-sample validation remains **not ready**.

The fixed non-drop 3-sample retry was approved and run on GPU0-bound `DISPLAY=:8`:

| Template | Command return | Validation |
|---|---:|---|
| collision | 0 | failed; no HDF5 |
| roll | 0 | failed; no HDF5 |
| containment | 0 | failed; no HDF5 |

The commands included `--run 1` and did not include drop-only arguments, but upstream non-drop generation still wrote no HDF5. Template-diverse 10 was not run, so 50 cannot be requested as a ready next step.

Next required work before 50: fix or parameterize upstream non-drop template generation so `collision`, `roll`, and `containment` produce valid HDF5 in the v2 wrapper.
