# TDW / Physion-style Moving-Camera v2 Generation Spec

## Terminology

Physion is TDW/ThreeDWorld simulation. v2 data should be called Physion-style TDW moving-camera simulation or Physion/TDW simulated clean GT. It is not real-world data.

## Output Structure

`local_assets/data/physion/generated_v2/`

- `raw_hdf5/`
- `videos/`
- `contact_sheets/`
- `manifests/`
- `lingbot_cam_inputs/`
- `reports/`
- `logs/`

## Profile 1: warmup_mild

Purpose: LingBot-Fast camera-conditioned warmup.

Requirements:

- smooth camera motion;
- small/medium yaw and translation;
- target object visible ratio >= 0.75;
- foreground should not leave frame for long;
- avoid extreme lookaway and `relative_yaw_180_reobserve`;
- camera motion can begin before/during physics event, but should not hide main object;
- suggested max yaw: 10-25 degrees;
- output RGB, depth, ID, camera_pose, intrinsics/projection, object_state, and prompt.

Explicit camera set:

- `orbit_left_12`
- `orbit_right_12`
- `strafe_left_025`
- `strafe_right_025`
- `dolly_in_010`
- `dolly_out_010`

These are the only variants allowed in `warmup_mild`. The wrapper rejects lookaway, offscreen, reobserve, relative-yaw-180, occluder, and extreme camera terms before generation.

Upstream mapping:

- orbit uses `camera_motion=orbit` and `camera_orbit_degrees=+/-12`;
- strafe uses `camera_motion=strafe` and `camera_strafe_distance=+/-0.25`;
- dolly uses the existing orbit/radius path with `camera_radius_delta=+/-0.10`.

## Profile 2: train_moderate

Purpose: later reward/DPO pair pool.

Requirements:

- moderate camera motion;
- target object visible ratio >= 0.6;
- allow some offscreen frames but reject complete disappearance;
- broader camera diversity than warmup.

## Profile 3: stress_reobserve

Purpose: test/stress split only.

Requirements:

- lookaway/offscreen/relative_yaw_180_reobserve allowed;
- object may leave frame but must reappear;
- target must be visible in first and reobserve segments;
- used for R_reobs and evaluation, not warmup main data.

## Profile 4: camera_only_static

Purpose: camera-following and rigid-background consistency tests.

Requirements:

- minimal foreground motion;
- camera moves;
- background should remain rigid and stable;
- good for R_bg and R_cam audits.

## Filtering Rules

Reject or mark as stress-only if:

- target_visible_ratio below profile threshold;
- target area too small;
- target disappears for too many consecutive frames;
- camera motion magnitude exceeds profile limits;
- camera jerk is too high;
- object completely offscreen for warmup;
- HDF5 keys incomplete;
- depth / ID / camera / object_state unavailable;
- frame count or duration invalid.

Every stage should output a validation report, contact sheet, storage estimate, and generation speed.

## Current Mild-Smoke Status

The `warmup_mild` plan dry-run is valid and contains no stress/reobserve variants. Actual TDW generation is gated on TDW display/GPU routing because the observed display `:8` appears to be configured on GPU0, while the current task only permits GPU6/7.

The wrapper now includes a display guard. A generation command must specify or inherit a display whose GPU is either detected as GPU6/7 or explicitly approved by the user. Unknown displays and GPU0-bound displays are blocked by default.

The approved GPU0 one-sample smoke did not produce data because the runtime wrapper failed before scene generation. No generated v2 sample should be treated as accepted until HDF5 validation succeeds.
