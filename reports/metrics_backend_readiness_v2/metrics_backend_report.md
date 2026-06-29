# Metrics Backend Readiness v2

Current Status: PASS_PARTIAL_FVD_VBENCH_BLOCKED_BY_ENV

## Matrix

- PSNR: PASS.
- SSIM: PASS.
- LPIPS: PASS.
- FVD: BLOCKED_BY_ENV. No real video FVD backend with local temporal feature weights is available. torchmetrics.video.FrechetVideoDistance unavailable: No module named 'matplotlib.axes' | pytorchvideo imports after lightweight install, but it does not provide an FVD metric or local I3D/FVD weights | pytorch-fid is installed, but image FID is not reported as video FVD
- VBench: BLOCKED_BY_ENV. VBench import failed: No module named 'vbench'

## Attempted Fixes

- Installed and checked pytorchvideo; it imports, but no real FVD metric or local I3D/FVD weights are available.
- Confirmed torchmetrics.video.FrechetVideoDistance is absent in torchmetrics 1.9.0.
- Confirmed pytorch-fid is image FID only and is not reported as video FVD.
- Searched local workspace for VBench; no usable VBench repo/assets were found.
- Did not start uncontrolled VBench/I3D model downloads.
