# TDW Generation v2 Non-Drop Output Discovery

Date: 2026-06-04

## Question

Did `collision`, `roll`, and `containment` truly write no HDF5, or did the wrapper/validator look in the wrong place?

## Discovery

The expected project output tree initially had no valid non-drop HDF5:

`local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_plan_3samples/`

However, HDF5 files were found under the upstream Physion workspace:

`/home/nvme03/workspace/physion_moving_camera_mainline_20260505/local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_plan_3samples/`

Files found there included:

- `00000_collision_orbit_left_12_seed22000/0000.hdf5`
- `00001_roll_orbit_right_12_seed22001/0000.hdf5`
- `00002_containment_strafe_left_025_seed22002/0000.hdf5`

## Cause

The subprocess current working directory was the upstream Physion workspace, but `--dir` was relative. The generated files were therefore placed under the upstream workspace's accidental `local_assets` directory.

## Fix

Make the wrapper pass absolute per-trial `--dir` paths and create the output directory before running TDW.

No generated HDF5 was moved or deleted.

