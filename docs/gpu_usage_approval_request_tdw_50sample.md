# GPU Usage Approval Request: TDW v2 50-Sample Validation

Generated: 2026-06-04

## Current 10-Sample Summary

- 10-sample `warmup_mild` generation passed on GPU0-bound `DISPLAY=:8`.
- Generated HDF5 count: 10.
- Validation ok count: 10.
- Rejected count: 0.
- target_visible_ratio avg/min/max: 1.0 / 1.0 / 1.0.
- max invisible frames max: 0.
- target.mp4 probe pass count after LingBot conversion: 10.
- Raw HDF5 storage for the 10 samples: 842M.
- Generation duration: 1266 sec.

## Why Approval Is Needed

The currently working TDW display is still GPU0-bound `DISPLAY=:8`. The previous approval covered exactly 10 samples and has now been consumed. Running 50 samples would be a longer GPU0-bound TDW job and is outside the current approval.

## Risk

- Expected runtime is roughly 5x the 10-sample smoke if runtime scales linearly.
- Expected raw HDF5 storage is roughly 4.1G to 4.3G for 50 samples.
- LingBot cam-only converted outputs may add several more GB.
- Current wrapper generated only `drop` templates in the 10-sample smoke despite the dry-run plan requesting multiple templates.

## Command If Approved

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --num_trials 50 \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allowed_gpu_ids 6,7 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

## Alternatives

1. Configure a GPU6/7 TDW display first.
2. Fix the template coverage issue before 50-sample validation.
3. Run a narrower 20-sample smoke to verify template coverage after wrapper fixes.

## Recommendation

Do not jump directly to 50 until the user confirms whether a drop-only 50-sample validation is acceptable. The safer next engineering step is to fix template coverage so `collision`, `roll`, and `containment` are actually generated.
