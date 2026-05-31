# DINOv2 Backend Smoke V3 Report

## Command

```bash
CUDA_VISIBLE_DEVICES=6,7 python -m cam_physgeo.rewards.feature_backend \
  --check dinov2 \
  --weights_root local_assets/weights \
  --out local_assets/reports/smoke/dinov2_backend_smoke_v3 \
  --device cuda \
  --limit 1 \
  --allow_download_small true \
  --model_name dinov2_vits14
```

## Result

- Local checkpoint before run: none
- Download performed: yes
- URL: `https://dl.fbaipublicfiles.com/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth`
- Target path: `local_assets/weights/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth`
- Size: `88283115` bytes
- HEAD content length: `88283115`
- Download elapsed: `63.165s`
- Full load+forward elapsed: `155.334s`
- Forward: success
- Feature shape: `[1, 384]`
- Missing keys: `0`
- Unexpected keys: `0`
- CUDA max memory allocated: `127773696` bytes

Torch hub downloaded the DINOv2 code cache into `local_assets/cache/torch`; model weights were saved under `local_assets/weights/dinov2`. No other model was downloaded.

## Reward Readiness

DINOv2-small can now provide real frame features for R_fg and R_reobs. Masking for generated videos is still proxy/global unless a generated segmentation/mask backend is added.
