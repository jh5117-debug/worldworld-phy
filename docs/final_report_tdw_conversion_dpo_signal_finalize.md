# Final Report: TDW Conversion + DPO Signal Finalize

Generated: 2026-06-04

## TDW 1-Sample

Passed.

- HDF5: `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_1samples/00000_drop_orbit_left_12_seed10000/0000.hdf5`
- Profile: `warmup_mild`
- Template: `drop`
- Camera variant: `orbit_left_12`
- HDF5 validation: passed
- Target visible ratio: `1.0`
- Max invisible frames: `0`
- Camera path length: `0.5927`
- Contact sheet: `local_assets/data/physion/generated_v2/reports/contact_sheets/00000_drop_orbit_left_12_seed10000_0000_contact_sheet.jpg`

LingBot cam-only conversion is now passed:

- target video: `local_assets/data/physion/generated_v2/lingbot_cam_inputs/tdw_v2_00000_drop_orbit_left_12_seed10000_0000/target.mp4`
- target.mp4 probe: passed
- frames / fps / size: `81 / 16.0 / 832x480`
- `poses.npy`: `(81, 4, 4)`
- `intrinsics.npy`: `(81, 4, 4)`
- `action.npy`: `(81, 4)`, norm `0.0`
- `metadata.json`: `use_action=false`

## TDW 10-Sample

Not run.

Approval is required because current TDW execution still depends on GPU0-bound `DISPLAY=:8`. The prior approval covered exactly one sample and has been consumed.

If approved, the intended command is:

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

Preferred alternative: configure a GPU6/7 TDW display and run the 10-sample smoke there.

## DPO Signal

`dpo_signal_sensitivity_fast` was launched on GPU6/7 and interrupted as a runtime blocker:

- model load began and entered the diagnostic runner;
- no `signal_sensitivity_fast_summary.json` was produced in the safe window;
- GPU6 peaked around `46.5 GiB`;
- no explicit OOM was observed;
- process was interrupted and GPU6/7 returned idle.

Signal gate: failed / incomplete.

## 5-Pair Go / No-Go

No-go.

The signal sweep did not complete at least two LR settings and did not demonstrate movement above the previous weak baseline. No 5-pair overfit was run.

## Gates

| Gate | Status |
|---|---|
| TDW 1-sample HDF5 | passed |
| TDW target.mp4 probe | passed |
| TDW LingBot cam-only conversion | passed |
| TDW 10-sample | approval required; not run |
| DPO signal fast sweep | runtime blocker |
| 5-pair tiny overfit | no-go |
| Full TDW generation | no |
| Real DPO training | no |

## Safety

- No training.
- No VideoGPA `03_train.py`.
- No Stage1.
- No LingBot rollout.
- No reward calibration.
- No 10/50 TDW generation.
- No LoRA or checkpoint saved.
- No `local_assets`, HDF5, MP4, NPY, latents, weights, or logs are committed.

## Next User Decision

Choose one:

1. Approve GPU0-bound `DISPLAY=:8` for exactly 10 TDW `warmup_mild` samples.
2. Configure a GPU6/7 TDW display before 10-sample generation.
3. Continue DPO signal runner optimization before any 5-pair overfit.
4. Pause generation and DPO diagnostics.
