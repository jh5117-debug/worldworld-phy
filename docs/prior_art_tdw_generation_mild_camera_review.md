# Prior-Art Review: TDW Generation Mild Camera Set

## Current Problem

The v2 warmup generation profile needs a mild-only camera set. The previous blocker was that the upstream batch runner did not expose an explicit `warmup_mild` / mild-only `camera_set`, so running it directly risked mixing stress/reobserve variants into warmup data.

## Files Checked

- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/scripts/batch_generate_physion_dpo_conditions.py`
- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/scripts/tdw_physion_multi_template_moving_camera.py`
- `cam_physgeo/data/tdw_generation_v2/`
- `configs/cam_physgeo/tdw_generation_v2.yaml`
- `scripts/31_run_tdw_generation_v2_smoke.sh`

## Upstream Camera Variants

The upstream batch runner defines `CAMERA_VARIANTS` internally. It includes mild variants such as:

- `orbit_left_20`
- `strafe_right_045`

It also includes stress/reobserve variants such as:

- `lookaway_up_reobserve`
- `offscreen_x_reobserve`
- `offscreen_z_reobserve`
- `occluder_lookaway_reobserve`
- `relative_yaw_180_reobserve`
- `relative_yaw_left_120_reobserve`

## Existing Upstream Camera Set Controls

The upstream runner has `--camera_set`, but the supported choices are stress-oriented:

- `all`
- `reobserve_only`
- `reobserve_no_occluder`
- `lookaway_only`
- `offscreen_z_only`
- `relative_yaw_180`
- `relative_reobserve`

There is no explicit mild-only set.

## Camera Parameter Entry Points

The upstream batch script eventually passes camera parameters to `tdw_physion_multi_template_moving_camera.py`:

- `--camera_motion`
- `--camera_orbit_degrees`
- `--camera_height_delta`
- `--camera_radius_delta`
- `--camera_strafe_distance`
- `--camera_lookaway_yaw_degrees`

The generation script supports orbit, strafe, radius-delta style dolly motion, and lookaway/reobserve variants. This means a wrapper can safely map mild names into upstream-compatible arguments without editing the upstream source.

## Mild / Warmup Candidates

The new `warmup_mild` set uses only:

- `orbit_left_12`
- `orbit_right_12`
- `strafe_left_025`
- `strafe_right_025`
- `dolly_in_010`
- `dolly_out_010`

The wrapper maps them to upstream `CAMERA_VARIANTS` dictionaries. Dolly is represented as `motion=orbit` with `camera_radius_delta=+/-0.10`, avoiding any requirement for a new upstream motion name.

## Banned Warmup Variants

`warmup_mild` explicitly bans variant names or motions containing:

- `lookaway`
- `offscreen`
- `relative_yaw_180`
- `relative_lookaway`
- `reobserve`
- `occluder`
- `extreme`

## Wrapper vs Patch

The least invasive solution is a wrapper:

1. Load the upstream batch runner at runtime through a generated wrapper script.
2. Replace `CAMERA_VARIANTS` in memory with the mild-only list.
3. Call upstream `main()` with `--camera_set all`, which now means "all mild injected variants".

This avoids modifying the upstream runner and avoids committing third-party/raw repo changes.

## GPU / Display Risk

The upstream runner uses `--display`, defaulting to `:8`. The current H20 check showed an Xorg process configured as `/etc/X11/tdw-xorg-gpu0.conf`, so actual TDW/Unity generation may use GPU0. This task only allows GPU 6/7. If no GPU 6/7 TDW display is available, actual generation must remain blocked and a GPU approval/display request must be written.

## Minimal Implementation Plan

- Add `camera_sets.warmup_mild` to `tdw_generation_v2.yaml`.
- Validate allowed and banned variants in `generation_config.py`.
- Write plan JSONL with explicit `camera_set`, `camera_variant`, `camera_motion`, and upstream mapping.
- Generate a runtime mild wrapper in `run_tdw_trial.py`.
- Block actual TDW execution if the configured display GPU is outside the allowed GPU set.

