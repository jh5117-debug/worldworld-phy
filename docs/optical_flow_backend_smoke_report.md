# Optical Flow Backend Smoke Report

## Result

- Local optical-flow assets: present.
- RAFT files detected under `local_assets/weights/optical_flow/RAFT`.
- Real learned RAFT/GMFlow/WAFT forward: not wired yet.
- Smoke fallback: OpenCV Farneback low-res flow.

## Smoke Output

- Output: `local_assets/reports/smoke/flow_backend_smoke/summary.json`
- Input video: `local_assets/data/physion/processed/lingbot_cam_inputs/smoke/physion_movingcam_07abddf5748b/target.mp4`
- Flow shape: `[1, 256, 448, 2]`
- Backend: `fallback`
- Confidence: `0.25`
- Mean magnitude: `0.0371`
- Max magnitude: `4.3106`
- Elapsed: `0.10s`

## Missing Work

The RAFT checkpoints exist, but no RAFT/GMFlow/WAFT loader is wired into `cam_physgeo` yet. R_bg, R_cam, and P_freeze must treat this path as fallback until a real optical-flow forward pass is implemented.
