Current Status: PASS

# FVD Real Smoke Summary

- Backend: TorchScript I3D VideoGPT variant
- I3D path: `/home/nvme03/workspace/world_model_phys/code/finetune_v3/lingbot-csgo-finetune/i3d_torchscript.pt`
- Input layout: `[B,3,T,H,W]`
- Clips: 4 winner videos vs 4 loser videos
- Feature shape: `(4, 400)` vs `(4, 400)`
- FVD smoke score: 0.6614066493904447
- Device: cuda:0
- Elapsed seconds: 30.21
- CSV: `reports/dpo_pair_factory_v11/metrics_backend_repair/fvd_real_smoke.csv`

This is a tiny backend verification smoke, not a stable benchmark FVD estimate.
