# Physion Data Audit

## Current Answer

- Official Physion repo: a non-git copy exists under `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/repos/physics-benchmarking-neurips2021`; a second non-git copy exists under `generation_functional_files_20260525/repos/physics-benchmarking-neurips2021`.
- Official standalone data root `/home/nvme03/workspace/physion_official/data`: not confirmed present during the audit.
- Official PhysionTest-Core / PhysionTest-Complete / train split: not confirmed present as standalone downloaded datasets.
- Existing Physion/TDW moving-camera root: `/home/nvme03/workspace/physion_moving_camera_mainline_20260505`.
- Existing moving-camera HDF5/H5 count: 1955.
- Existing moving-camera MP4 count: 369.
- `commandline_args.txt` count: 2119.
- `tdw_commands.json` count: 2186.
- `summary.json` count: 92.
- `batch_config.json` count: 72.
- Existing moving-camera data size: about 198 GB.

## Interpretation

The standalone official Physion dataset still needs a separate download/check if we want Core/Complete coverage. The current stage can proceed without it because the local Physion/TDW moving-camera HDF5 already contains RGB, depth, ID, camera pose, projection/camera matrices, object states, collisions, and reobserve camera motions.

No CSGO or PhyInOne data is part of the active pipeline.
