# GPU Usage Approval Request: TDW v2 10-Sample Smoke

## Task

Run `warmup_mild` TDW / Physion-style generation v2 10-sample smoke.

## Why Approval Is Needed

The only working TDW display found so far is `DISPLAY=:8`, which is bound to
GPU0. The user previously approved GPU0 only for exactly one sample. That
approval was consumed by the successful 1-sample smoke.

## Current Evidence

- 1-sample generation passed on `DISPLAY=:8`.
- Generated HDF5 validated successfully.
- Target visible ratio: `1.0`.
- Max invisible frames: `0`.
- Camera path length: `0.5927`.
- LingBot cam-only conversion now passed.
- `target.mp4` probe passed: 81 frames, 16 fps, 832x480.
- `metadata.json` keeps `use_action=false`; `action.npy` is dummy zero, norm `0.0`.

## Requested Command

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

## Expected Usage

| Item | Estimate |
|---|---|
| GPU | GPU0 via `DISPLAY=:8` |
| Scale | 10 samples only |
| Time | unknown until smoke; likely longer than 1-sample |
| Memory | 1-sample used roughly TDW/Unity-level graphics memory; not LingBot training memory |
| Training | no |
| DPO | no |
| Saved weights/checkpoints | no |

## Alternatives

1. Configure a TDW display on GPU6/7 and run 10-sample there.
2. Pause TDW generation and continue DPO signal diagnostics on GPU6/7 only.
3. Keep only the accepted 1-sample for presentation/warmup inspection.

## Required User Choice

User must explicitly approve one of:

- Approve GPU0-bound `DISPLAY=:8` for 10-sample warmup_mild smoke.
- Configure GPU6/7 TDW display first.
- Pause TDW generation.
