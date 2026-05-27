# Physion Official Download Report

Status as of this refactor:

- Official project URL: `https://github.com/cogtoolslab/physics-benchmarking-neurips2021`
- Existing local non-git repo copy: `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/repos/physics-benchmarking-neurips2021`
- Standalone clone target: `/home/nvme03/workspace/physion_official/physics-benchmarking-neurips2021`
- Clone attempt: network/SSH session stalled during this run, so no new clone commit hash was recorded.
- Standalone dataset root: `/home/nvme03/workspace/physion_official/data`
- Dataset download status: not launched.
- PhysionTest-Core / Complete status: not confirmed present.
- Current local moving-camera data is sufficient for HDF5 reader, cam-only converter, reward, corruption, and DPO smoke tests.

Do not download Physion-Complete automatically until package size and disk impact are reviewed. `/home/nvme03` had about 951 GB free during audit, but Complete-size downloads still need explicit logging and staged verification.
