# Physion Regeneration Code Audit

The existing moving-camera project contains TDW/Physion generation artifacts and command logs:

- `commandline_args.txt`: 2119 files
- `tdw_commands.json`: 2186 files
- `summary.json`: 92 files
- `batch_config.json`: 72 files

The HDF5 files already contain moving-camera metadata for the current smoke path, including `camera_pose`, `camera_position`, `camera_aim`, and camera/projection matrices. Large-scale regeneration is not needed for the first Physion-only smoke pipeline.

The new script `scripts/12_generate_physion_movingcam_subset.sh` and module `cam_physgeo.data.physion_regenerate_plan` only audit candidate generation scripts and print a dry-run plan. They do not overwrite existing data.
