# Final Report: TDW GPU6/7 Visible-Motion Smoke

Date: 2026-06-05

## GPU / Display

No GPU6/7 TDW display exists yet.

Current verified TDW display:

```text
DISPLAY=:8
```

Binding:

```text
/etc/X11/tdw-xorg-gpu0.conf
```

Therefore `DISPLAY=:8` is GPU0-bound and was not used.

GPU6 / GPU7 status:

- GPU6: `00000000:CA:00.0`, idle.
- GPU7: `00000000:DA:00.0`, idle.

Passwordless sudo is unavailable:

```text
sudo: a password is required
sudo_not_available
```

Because creating `/etc/X11/tdw-xorg-gpu6.conf` and starting `Xorg :16` require sudo/admin access, setup was blocked.

## Existing 50 Reassessment

The existing template-diverse 50-sample batch is still a pipeline validation pass, but its camera motion is too weak for final warmup main data.

It should not be expanded to 200/1k.

## Visible-Motion Profile

Profile:

`warmup_visible_motion`

Variants:

- `orbit_left_24`
- `orbit_right_24`
- `orbit_left_28`
- `orbit_right_28`
- `strafe_left_050`
- `strafe_right_050`
- `dolly_in_025`
- `dolly_out_025`

Thresholds:

- `target_visible_ratio >= 0.75`
- `max_invisible_frames <= 8`
- `camera_path_length >= 0.45`
- `camera_path_length <= 1.50`
- `background_motion_proxy >= 0.012`
- `video_motion_proxy >= 0.015`

## Plan

The 10-sample `warmup_visible_motion` plan check passed:

- `drop:3`
- `collision:3`
- `roll:2`
- `containment:2`
- `bad_count=0`

## Actual Generation

Not run.

| Gate | Status |
|---|---|
| GPU6/7 display | blocked |
| 1-sample actual | not run |
| 10-sample actual | not run |
| conversion | not run |
| video deliverables | no new visible-motion videos |

## Safety

- GPU0 was not used.
- No training.
- No DPO.
- No VideoGPA `03_train.py`.
- No Stage1.
- No reward calibration.
- No 50/200/1k generation.
- No generated HDF5/MP4/NPY committed.
- No `local_assets` committed.

## Next Action

An administrator should create a GPU6 or GPU7 TDW Xorg display, preferably:

```text
DISPLAY=:16 on GPU6
```

GPU6 Xorg BusID:

```text
PCI:202:0:0
```

After setup, rerun:

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_visible_motion \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_1.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display :16 \
  --allowed_gpu_ids 6,7 \
  --require_allowed_gpu_display \
  --no_overwrite
```

Only after the 1-sample visible-motion smoke passes should the 10-sample visible-motion smoke run.
