# Reward Calibration v2 Report

## Implementation / Smoke Update - 2026-06-24 16:45 CST

Added `cam_physgeo.eval.reward_calibration_v2`, which generates real corrupted videos for supported corruptions and evaluates clean GT versus corrupted candidates through `cam_physgeo.eval.quant_benchmark_v1`. It does not fake missing tracker or geometry backends.

Smoke run:

- manifest: `manifests/quant_benchmark_v1_core.jsonl`
- limit: 2 conditions
- corruptions: `background_drift`, `freeze_camera`
- geometry: skipped for speed
- output: `reports/reward_calibration_v2/smoke_2_skip_geometry/`
- clean > corrupted rates: PSNR 1.0, SSIM 1.0, pixel-L1 1.0, freeze-rate 1.0, quality-proxy 1.0
- Epipolar/C-SGC: null because geometry was skipped

Status: smoke PASS, full Reward Calibration v2 still pending before DPO-ready claims.
