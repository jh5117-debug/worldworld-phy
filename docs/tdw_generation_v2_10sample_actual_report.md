# TDW Generation v2 10-Sample Actual Report

Generated: 2026-06-04

## Approval

The user explicitly approved using current GPU0-bound `DISPLAY=:8` for exactly 10 `warmup_mild` TDW / Physion-style generation v2 smoke samples.

No 50/200/1k generation was run.

## Generation Command

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

## Runtime

| Item | Value |
|---|---:|
| Return code | 0 |
| Duration | 1266 sec |
| GPU used | GPU0 via `DISPLAY=:8` |
| GPU before | GPU0 845 MiB, 0% util |
| GPU after | GPU0 28 MiB, 0% util |
| Raw HDF5 storage | 842M |

## Generation Counts

| Metric | Value |
|---|---:|
| Requested samples | 10 |
| Generated HDF5 count | 10 |
| Validation ok count | 10 |
| Failed count | 0 |
| Rejected count | 0 |
| Suitable for warmup | 10 |

## Distributions

Template distribution:

| Template | Count |
|---|---:|
| drop | 10 |

Camera variant distribution:

| Camera variant | Count |
|---|---:|
| orbit_left_12 | 2 |
| orbit_right_12 | 2 |
| strafe_left_025 | 2 |
| strafe_right_025 | 2 |
| dolly_in_010 | 1 |
| dolly_out_010 | 1 |

The actual runner did not cover `collision`, `roll`, or `containment` despite the dry-run plan requesting them. This is a wrapper/upstream coverage issue to fix before broader generation.

## Validation Metrics

| Metric | Avg | Min | Max |
|---|---:|---:|---:|
| target_visible_ratio | 1.0 | 1.0 | 1.0 |
| camera_path_length | 0.3575 | 0.1005 | 0.5927 |

| Metric | Value |
|---|---:|
| max invisible frames avg | 0.0 |
| max invisible frames max | 0 |

## HDF5 Key Completeness

All 10 samples have:

- RGB / `_img`
- `_depth`
- `_id`
- camera pose
- camera position
- camera aim
- projection / camera matrix
- object state

## Contact Sheets

Contact sheets were written under:

`local_assets/data/physion/generated_v2/reports/contact_sheets/`

Representative files:

- `00000_drop_orbit_left_12_seed10000_0000_contact_sheet.jpg`
- `00004_drop_dolly_in_010_seed10000_0000_contact_sheet.jpg`
- `00009_drop_strafe_right_025_seed10001_0000_contact_sheet.jpg`

## Sample HDF5 Paths

- `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_10samples/00000_drop_orbit_left_12_seed10000/0000.hdf5`
- `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_10samples/00001_drop_orbit_right_12_seed10000/0000.hdf5`
- `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_10samples/00002_drop_strafe_left_025_seed10000/0000.hdf5`
- `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_10samples/00003_drop_strafe_right_025_seed10000/0000.hdf5`
- `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_10samples/00004_drop_dolly_in_010_seed10000/0000.hdf5`
- `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_10samples/00005_drop_dolly_out_010_seed10000/0000.hdf5`
- `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_10samples/00006_drop_orbit_left_12_seed10001/0000.hdf5`
- `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_10samples/00007_drop_orbit_right_12_seed10001/0000.hdf5`
- `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_10samples/00008_drop_strafe_left_025_seed10001/0000.hdf5`
- `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_10samples/00009_drop_strafe_right_025_seed10001/0000.hdf5`

## Gate Decision

TDW v2 10-sample `warmup_mild` smoke passed for camera mildness, visibility, and HDF5 completeness.

Remaining issue before 50-sample: fix or explicitly accept template coverage, because this smoke produced only `drop` samples.
