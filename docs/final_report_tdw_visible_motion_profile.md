# Final Report: TDW Visible-Motion Profile

Date: 2026-06-05

## Existing 50 Reassessment

The previous template-diverse 50-sample batch remains useful as a pipeline validation set:

- HDF5 validation passed;
- LingBot cam-only conversion passed;
- target.mp4 probing passed.

However, it is not final warmup main data because camera motion is visually too weak. The main issue is that `warmup_mild` used 12-degree orbit, 0.25 strafe, and 0.10 dolly motions. These are too close to static videos for the intended camera-conditioned world-model warmup.

## New Profile

Added:

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

This profile is stronger than `warmup_mild` but still bans lookaway, offscreen, reobserve, relative-yaw-180, occluder, and extreme camera behavior.

## Validator

Added visible-motion validation fields:

- camera path length;
- yaw proxy;
- RGB video motion proxy;
- background/parallax proxy;
- `too_static`;
- `too_extreme`;
- `suitable_for_visible_motion`.

Acceptance thresholds:

- `target_visible_ratio >= 0.75`;
- `max_invisible_frames <= 8`;
- `min_camera_path_length >= 0.45`;
- `max_camera_path_length <= 1.50`;
- `min_background_motion_proxy >= 0.012`;
- `min_video_motion_proxy >= 0.015`.

## Plan

`warmup_visible_motion` 10-sample dry-run passed:

- `drop:3`
- `collision:3`
- `roll:2`
- `containment:2`
- `bad_count=0`

## GPU / Display

Actual generation was not run.

Reason:

- the only verified TDW Xorg display is `DISPLAY=:8`;
- it is bound to GPU0 via `/etc/X11/tdw-xorg-gpu0.conf`;
- no GPU6/7 TDW display config was found;
- this turn forbids GPU0-5.

GPU0 was not used.

## Generation

- actual visible-motion samples generated: 0
- conversion: not run
- video deliverables: no new visible-motion videos added

## Safety

- no training;
- no DPO training;
- no VideoGPA `03_train.py`;
- no Stage1;
- no LingBot rollout;
- no reward calibration;
- no GPU0 generation;
- no 50/200/1k generation;
- no local_assets committed.

## Next Action

Configure a TDW display on GPU6 or GPU7, then run:

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_visible_motion \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_10.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display <GPU6_OR_GPU7_DISPLAY> \
  --allowed_gpu_ids 6,7 \
  --require_allowed_gpu_display \
  --no_overwrite
```

If the 10-sample visible-motion smoke passes visually and by validator, the next staged step can be a user-approved visible-motion 50-sample validation.
