# Metrics Backend Readiness

Updated: 2026-06-29 11:58:36

## Summary

- PSNR: PASS.
- SSIM: PASS.
- LPIPS: PASS.
- FVD: BLOCKED_BY_ENV. pytorch-fid is available, but no real video FVD backend is installed; FID is not reported as FVD.
- VBench: BLOCKED_BY_ENV. VBench import failed: No module named 'vbench'

## Notes

- PSNR and SSIM are mandatory and passed the local smoke test.
- LPIPS was installed and smoke-tested if the runtime could load its local weights.
- FVD is not reported from `pytorch-fid`; image FID is not a valid replacement for video FVD.
- VBench is not auto-downloaded because it may require large assets/configuration; missing backend is reported as blocked rather than fabricated.
