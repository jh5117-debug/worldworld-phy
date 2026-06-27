# EXP V2V-5 StageA Warmup

Status: prepared

Question: can LingBot-Fast use a real 5-frame prefix plus camera poses/intrinsics to predict frames 5-80 without falling back to image-only conditioning?

Settings: V2V-5, camera-conditioning LoRA only, rank 4, alpha 4, dropout 0.05, high-noise-only, future-only loss.

Gate: wrapper proof must show prefix frames 0-4 encoded and future frames zeroed; every checkpoint needs real V2V-5 rollout, Codex audit, PSNR/SSIM, and available LPIPS/FVD/VBench/PhysGeo metrics.
