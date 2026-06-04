# Prior Art Review: Non-Drop TDW Template Generation

Date: 2026-06-04

## Upstream Code

Reviewed upstream repository:

`/home/nvme03/workspace/physion_moving_camera_mainline_20260505`

Main runner:

`scripts/tdw_physion_multi_template_moving_camera.py`

Relevant mapping:

| v2 template | Upstream class / template |
|---|---|
| `drop` | `MovingCameraDrop` / `Drop` |
| `collision` | `MovingCameraCollision` / `Collision` |
| `roll` | `MovingCameraRollingSliding` / `RollingSliding` |
| `containment` | `MovingCameraContainment` / `Containment` |

The upstream runner only executes generation when `--run 1` is present.

## Native Non-Drop Arguments

Successful native non-drop samples use template-specific arguments. The wrapper must not send drop-only arguments to non-drop templates, but it must provide the upstream non-drop defaults needed to construct a valid stimulus.

| Template | Required native-style args used in v2 wrapper |
|---|---|
| `collision` | `--only_use_flex_objects`, `--collision_axis_length 2`, `--frot [-8,8]`, `--fscale [5.0,11.0]`, `--fupforce [0.0,0.0]`, `--target pyramid,cone,dumbbell,triangular_prism,torus`, `--pmass 4`, `--monochrome 1`, `--random 0`, `--seed 328`, `--no_moving_distractors`, `--room box` |
| `roll` | `--only_use_flex_objects`, `--collision_axis_length 1.7`, `--probe ...`, `--target ...`, `--prot [-180,180]`, `--tlift 0.25`, `--fscale [2.,9.]`, `--frot [-3,3]`, `--camera_distance [2.3,2.5]`, `--monochrome 1`, `--random 0`, `--seed 914`, `--no_moving_distractors`, `--room box` |
| `containment` | `--fwait 15`, `--random 0`, `--seed 1`, `--only_use_flex_objects`, middle/base/distractor/occluder category args, `--num_distractors 1`, `--num_occluders 1` |

## Root Cause Found

The upstream native probe wrote HDF5 for all three non-drop templates, proving the upstream runner was usable.

The v2 wrapper still reported `returncode=0` and `hdf5=None` because it passed `--dir local_assets/...` while launching the subprocess with `cwd` set to the upstream Physion workspace. That relative path resolved under:

`/home/nvme03/workspace/physion_moving_camera_mainline_20260505/local_assets/...`

instead of the project tree:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/...`

So HDF5 files were written, but to the wrong workspace.

## Minimal Fix

The wrapper now resolves each per-trial output directory to an absolute path before passing it to upstream TDW:

`--dir /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/...`

It also creates the per-trial output directory before subprocess launch.

