# DPO Objective Smoke v3 Report

Current Status: BLOCKED_WAITING_FOR_GPU_CAPACITY
Updated: 2026-06-29 15:39:49

## Gate Status

- Protocol v3 pair count: 34, all Type A.
- LocalDPO spatial mask v2: PASS, 34 usable spatial+time masks.
- Metrics backend: PSNR/SSIM/LPIPS PASS; FVD/VBench BLOCKED_BY_ENV with attempted fixes recorded.
- DPO BF16 backend: previously PASS.
- GPU capacity: BLOCKED. GPUs 0-7 are occupied by unrelated LIBERO evaluation processes.

## Decision

Do not start DPO smoke while GPUs are occupied. Once capacity is available, run only `DPO_smoke_v3_8` with SDPO-anchor v2, max 10 steps, and true V2V-5 checkpoint video evaluation. No large-scale DPO.
