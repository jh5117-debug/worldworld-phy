# TDW GPU6/7 Display Options

## Option A: Use Existing GPU6/7 Display

Status: not available.

The server has Xvfb displays `:9` to `:13`, but no running Xorg display bound to GPU6 or GPU7. `DISPLAY=:9` uses Mesa llvmpipe, not NVIDIA GPU6/7.

If a GPU6/7 Xorg display is later provided, run only a display check first:

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_mild \
  --num_trials 1 \
  --out_root local_assets/data/physion/generated_v2 \
  --display <GPU6_OR_GPU7_DISPLAY> \
  --allowed_gpu_ids 6,7 \
  --require_allowed_gpu_display \
  --no_run_if_display_gpu_mismatch \
  --dry-run-display-check \
  --no_overwrite
```

## Option B: Create / Configure TDW Display On GPU6/7

Status: needs admin/system setup.

Likely requirements:

- create an Xorg config similar to `/etc/X11/tdw-xorg-gpu0.conf`, but using GPU6 or GPU7 BusID;
- start Xorg on a free display such as `:14`;
- verify with `xdpyinfo`, `glxinfo -B`, and the wrapper display guard;
- ensure the display does not interfere with other users.

Risk:

- requires root/sudo or system-level service changes;
- wrong BusID could bind the wrong GPU;
- should not be attempted by this task without user/admin confirmation.

## Option C: User Approves Current GPU0-Bound Display For One Sample

Status: requires explicit user approval.

The current TDW display `:8` is GPU0-bound. If the user approves, the next run should be limited to exactly one `warmup_mild` sample:

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

Do not run 10/50 samples under this option without a separate confirmation.

