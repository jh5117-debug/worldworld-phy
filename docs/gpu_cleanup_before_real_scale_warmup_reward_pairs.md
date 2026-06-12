# GPU Cleanup Before Real-Scale Warmup / Reward-Pair Pipeline

Date: 2026-06-11

## Audit

H20 GPU audit before Stage A:

- GPU4: free
- GPU5: free
- GPU6: free
- GPU7: free

No GPU4-7 training, LingBot, cam_physgeo, VideoGPA, or DPO process required cleanup.

## Action

- No process was killed.
- GPU0-3 had unrelated existing processes and were not touched.
- Xorg, ssh, systemd, docker, and unknown/system processes were not touched.

## Intended Use

- Stage A warmup uses GPU7 through `CUDA_VISIBLE_DEVICES=7`.
- GPU0 is not used for LingBot warmup.
