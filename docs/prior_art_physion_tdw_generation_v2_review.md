# Prior Art: Physion / TDW Generation v2 Review

## Current Problem

We need a staged Physion-style TDW moving-camera generation pipeline that can create warmup-friendly clips before any large-scale generation or training. The current stress sample in the presentation has extreme camera motion and foreground disappearance, so it is not suitable for warmup.

## Local Sources Checked

Local generation sources found:

- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505`
- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/repos/tdw_physics`
- `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/repos/physics-benchmarking-neurips2021`
- `local_assets/third_party/physion_official_repo`
- `local_assets/data/physion/movingcam_raw`
- `local_assets/data/physion/movingcam_outputs`
- project scripts under `cam_physgeo/` and `scripts/`.

## Physion / TDW Relationship

Physion is a TDW / ThreeDWorld / Unity3D simulation benchmark, not real-world captured video. The official Physion code organizes benchmark stimuli and depends on TDW/tdw_physics generation. Our current moving-camera data is a project extension built from Physion-style TDW scenes.

## TDW / tdw_physics Dependency

The local moving-camera workspace includes:

- `repos/tdw_physics`, with target controllers such as drop, collide/collision, roll, contain/containment;
- TDW Python runtime through the `tdw` package;
- a local `.conda_envs/tdw-physion` Python environment;
- X display usage such as `DISPLAY=:8` for TDW/Unity rendering.

## Existing Moving-Camera Scripts

Key scripts:

- `scripts/batch_generate_physion_dpo_conditions.py`: batch wrapper that creates `manifest.jsonl`, `summary.json`, trial directories, and HDF5 outputs.
- `scripts/tdw_physion_multi_template_moving_camera.py`: TDW controller extension for multi-template moving camera generation.
- `scripts/tdw_physion_support_moving_camera.py`: support moving-camera controller variant.
- `scripts/hdf5_to_video.py`: HDF5-to-video conversion.
- `scripts/prepare_lingbot_physion_inputs.py`: conversion toward LingBot camera inputs.

## HDF5 Generation and Camera Metadata

`tdw_physics` writes trial HDF5 files under per-trial directories, usually as `0000.hdf5`. Existing HDF5 checks confirm `_img`, `_depth`, `_id`, `camera_position`, `camera_aim`, and `camera_pose` can be written. The moving-camera controller logs TDW camera commands such as `teleport_avatar_to`, `look_at_position`, and `set_focus_distance`.

## Existing Camera Variants

Existing variants include mild and stress motions:

- mild-ish: `orbit_left_20`, `strafe_right_045`;
- stress/reobserve: `lookaway_up_reobserve`, `offscreen_x_reobserve`, `offscreen_z_reobserve`, `occluder_lookaway_reobserve`, `relative_yaw_180_reobserve`, `relative_yaw_left_120_reobserve`, `relative_yaw_right_120_reobserve`.

The current batch script exposes `camera_set` options for all/reobserve/relative/offscreen/lookaway, but does not expose an explicit mild-only set. This is the main reason the v2 wrapper refuses actual `warmup_mild` generation unless mild-only support is explicit.

## Templates Available

The reusable templates are:

- drop;
- collision / collide;
- roll;
- containment / contain.

These map to tdw_physics target controllers and Physion-style physical events.

## Why the Current Strong Reobserve Sample Is Not Warmup Data

The presentation's clean GT example is useful as a stress/test sample, but it has too much camera motion for warmup and can hide the main object. Warmup should teach stable camera-conditioned physical prediction, so the main target should remain visible in most frames.

## Reusable Code

Reusable:

- existing TDW/tdw_physics controllers;
- current moving-camera controller mixin;
- HDF5 generation and key checks;
- HDF5-to-video conversion;
- LingBot cam-input conversion utilities.

Needs wrapper/filter:

- explicit mild camera profiles;
- target-visible-ratio filtering;
- max camera yaw/translation/jerk limits;
- no-overwrite output roots;
- staged reports for 1/10/50 samples.

## Minimum v2 Implementation Plan

1. Add a config-driven v2 profile spec.
2. Add a dry-run planner.
3. Add a conservative runner that refuses warmup generation if mild-only selection is not guaranteed.
4. Add HDF5 validator and filtering reports.
5. Add deliverable video index/gallery.
6. Only after 1-sample and 10-sample validation should 50-sample validation run.
