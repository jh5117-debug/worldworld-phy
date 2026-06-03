# TDW Generation v2 Display Guard Report

## Purpose

Prevent the generation wrapper from accidentally launching TDW/Unity on GPU0 when the task allows only GPU6/7.

## Files Updated

- `configs/cam_physgeo/tdw_generation_v2.yaml`
- `cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py`
- `scripts/31_run_tdw_generation_v2_smoke.sh`

## New Parameters

`run_tdw_trial.py` now supports:

- `--display`
- `--allowed_gpu_ids`
- `--require_allowed_gpu_display`
- `--dry-run-display-check`
- `--no_run_if_display_gpu_mismatch`
- `--allow_unapproved_gpu`
- `--gpu_confirmation_token`

`scripts/31_run_tdw_generation_v2_smoke.sh` forwards:

- `--display`
- `--allowed_gpu_ids`
- `--require_allowed_gpu_display`
- `--dry-run-display-check`
- `--no_run_if_display_gpu_mismatch`

## Default Policy

- Allowed GPU IDs default to `6,7`.
- `DISPLAY=:8` maps to GPU0 in config.
- If the detected display GPU is not in the allowed set, the run is blocked before Unity starts.
- If the display GPU cannot be detected, the run is blocked when `--require_allowed_gpu_display` is set.
- Unapproved GPU use requires both `--allow_unapproved_gpu` and the explicit token `USER_CONFIRMED_UNAPPROVED_GPU`; this is intentionally awkward so it cannot happen by accident.

## Metadata Logged

Each run report records:

- `tdw_display`
- `tdw_display_gpu_index`
- `display_detection`
- `allowed_gpu_indices`
- `require_allowed_gpu_display`
- `no_run_if_display_gpu_mismatch`
- `blocked_reason`
- full command

## Remote Display Check Result

Running the guard on `DISPLAY=:8` returned:

- `xorg_process_found`: true
- `xorg_config`: `/etc/X11/tdw-xorg-gpu0.conf`
- `gpu_index`: 0
- `allowed_gpu_indices`: `[6, 7]`
- status: `blocked`

No Unity process was launched.

## How To Specify A GPU6/7 Display Later

Example command after a GPU6/7 display exists:

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --num_trials 1 \
  --out_root local_assets/data/physion/generated_v2 \
  --display :9 \
  --allowed_gpu_ids 6,7 \
  --require_allowed_gpu_display \
  --no_run_if_display_gpu_mismatch \
  --no_overwrite
```

This should only be used if `:9` is proven to be an NVIDIA Xorg display on GPU6 or GPU7. The current `:9` is Xvfb/llvmpipe and is not a confirmed TDW path.

