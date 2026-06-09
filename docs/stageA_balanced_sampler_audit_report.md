# Stage A Balanced Sampler Audit

Date: 2026-06-09

## Old Sampler Behavior

The previous Stage A pilot selected train samples sequentially from the manifest. Because the current train split is grouped by template/camera for its first rows, the first 20 steps were all:

`collision + orbit_right_64`

This made the previous run a valid stability smoke, but not a balanced template/camera pilot.

## Root Cause

The training loop used manifest order directly:

`train_rows[(step - 1) % len(train_rows)]`

There was no shuffle seed, epoch shuffle, balanced key, or template/camera coverage guarantee.

## New Sampler Design

`cam_physgeo/training/lingbot_warmup_smoke.py` now supports:

- `--mode sampler_dryrun`
- `--sampler sequential|shuffle|balanced`
- `--balance_keys template,camera_variant`
- `--shuffle_seed`
- `--sample_without_replacement true`
- `--log_sample_ids`
- `--log_template_camera_stats`

The balanced sampler:

- groups rows by template and camera variant;
- rotates templates in the order `drop`, `collision`, `roll`, `containment`;
- rotates camera groups within each template;
- shuffles rows inside groups with a fixed seed;
- avoids duplicates while enough samples are available.

## Expected Coverage

For a 60-step Stage A run:

- first 20 should contain at least 3 templates;
- first 60 should contain all 4 templates;
- first 60 should contain at least 4 camera variants;
- duplicates should be avoided.

## Limitations

The sampler balances observed manifest metadata. It does not create new samples and cannot fix source distribution if a template has only one camera variant in the split. The current split has enough metadata for the Stage A balanced gate.
