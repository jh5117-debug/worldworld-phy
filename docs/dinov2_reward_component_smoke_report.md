# DINOv2 Reward Component Smoke Report

## Command

```bash
CUDA_VISIBLE_DEVICES=6,7 python -m cam_physgeo.rewards.score_video \
  --manifest local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl \
  --source physion_movingcam \
  --out local_assets/reports/smoke/dinov2_reward_component_smoke.jsonl \
  --limit 3 \
  --save_debug_vis \
  --require_feature_backend true \
  --feature_backend dinov2 \
  --device cuda
```

## Result

- Rows scored: `3`
- DINO checkpoint: `local_assets/weights/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth`
- Feature shape in reward rows: `[4, 384]`
- R_fg backend: `real_dino_id_mask`
- R_reobs backend: `real_dino_reobserve_proxy_segments`
- R_fg confidence: `0.85` when clean ID mask exists.
- R_reobs confidence: `0.6` because visible/reobserve segments are still first/last proxy segments.

## Caveats

DINO forward is real. Generated-video masks and reobserve segment localization are still proxy. The next fidelity improvement is generated mask/track propagation or SAM/ID propagation, not more DINO downloading.
