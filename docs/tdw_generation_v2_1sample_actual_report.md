# TDW Generation v2 1-Sample Actual Report

## Status

Passed for actual TDW generation and HDF5 validation.

This run used the user-approved GPU0-bound `DISPLAY=:8` for exactly one
`warmup_mild` sample. No 10-sample or 50-sample generation was run.

## Generation Command

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --num_trials 1 \
  --out_root local_assets/data/physion/generated_v2 \
  --display :8 \
  --allowed_gpu_ids 6,7 \
  --allow_unapproved_gpu \
  --gpu_confirmation_token USER_CONFIRMED_UNAPPROVED_GPU \
  --no_overwrite
```

## Output

| Item | Value |
|---|---|
| Status | passed |
| Profile | `warmup_mild` |
| Template | `drop` |
| Camera variant | `orbit_left_12` |
| Display | `:8` |
| Detected GPU | GPU0 |
| HDF5 | `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_1samples/00000_drop_orbit_left_12_seed10000/0000.hdf5` |
| HDF5 size | about 89 MB |
| MP4 from generation | not emitted by upstream runner |
| Contact sheet | `local_assets/data/physion/generated_v2/reports/contact_sheets/00000_drop_orbit_left_12_seed10000_0000_contact_sheet.jpg` |

## Validation

Validated with the TDW environment Python because the system Python did not
have `h5py`.

| Check | Result |
|---|---|
| HDF5 count | 1 |
| Validation ok count | 1 |
| Suitable for warmup count | 1 |
| Frame count | 83 |
| RGB `_img` | true |
| `_depth` | true |
| `_id` | true |
| `camera_pose` | true |
| `camera_position` / `camera_aim` | true |
| projection / camera matrix | true |
| object state | true |
| target visible ratio | 1.0 |
| max consecutive invisible frames | 0 |
| camera path length | 0.5927 |

## Interpretation

This sample is a valid Physion-style TDW simulated clean GT sample. It uses the
new mild camera set, keeps the target visible for all frames, and is suitable
for warmup validation.

10-sample smoke was not run in this pass because the current available TDW
display is still GPU0-bound and multi-sample GPU0 use requires separate user
approval.
