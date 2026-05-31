# Optical Flow Backend Smoke V2 Report

## Asset Discovery

- Optical-flow root: `local_assets/weights/optical_flow`
- RAFT repo/assets found: yes
- Preferred checkpoint: `local_assets/weights/optical_flow/RAFT/models/raft-small.pth`
- Candidate checkpoints:
  - `raft-small.pth`
  - `raft-sintel.pth`
  - `raft-kitti.pth`
  - `raft-things.pth`
  - `raft-chairs.pth`

## Smoke Result

- Backend selected: RAFT-small
- Real forward: yes
- Input video: `local_assets/data/physion/processed/lingbot_cam_inputs/smoke/physion_movingcam_07abddf5748b/target.mp4`
- Resolution: `256x448`
- Flow shape: `[1, 256, 448, 2]`
- Mean magnitude: `7.447540760040283`
- Std magnitude: `4.038685321807861`
- Max magnitude: `27.303043365478516`
- Elapsed: `11.370122194290161` seconds
- CUDA max memory allocated: `82245632` bytes
- Output summary: `local_assets/reports/smoke/flow_backend_smoke_v2/summary.json`

## Notes

The initial RAFT attempt failed because the copied RAFT code imports from `update.py` under its `core/` directory. The backend now adds both the RAFT root and `core/` to `sys.path`. A second failure from RAFT's argument container was fixed by adding a small namespace wrapper with `__contains__`.

This is a real learned optical-flow forward and is now usable as a minimal backend for R_bg, R_cam, and P_freeze proxies. It is still not a full rigid-flow residual because generated-video depth is not yet available.
