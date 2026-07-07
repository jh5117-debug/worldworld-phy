# E02_best7 Metrics Summary

- PSNR/SSIM rows: `12/12` OK, computed against repaired full81 references from `clip_dir/video.mp4`.
- PSNR mean: `13.497703451157209`
- SSIM mean: `0.6916122233717971`
- LPIPS GPU smoke: `PASS`, rows `12/12`, mean `0.5917419865727425`.
- FVD: `BLOCKED_BY_ENV`; no valid local video-FVD backend was available in this v14 eval wrapper, and image FID was not substituted.
- VBench: package import available, but real checkpoint scoring was not configured in this wrapper.

Metric gate is partial only. Combined with visual degradation, E02_best7 is not a valid scalable DPO recipe.
