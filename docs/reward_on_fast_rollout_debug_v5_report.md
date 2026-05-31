# Reward On Fast Rollout Debug V5 Report

## Command

```bash
CUDA_VISIBLE_DEVICES=6,7 python -m cam_physgeo.eval.eval_fast_rollouts \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --rollouts local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke \
  --out local_assets/reports/reward_calibration/fast_zero_shot_reward_debug_v5 \
  --limit 3 \
  --save_debug \
  --gpu_ids 6,7 \
  --debug_reward_breakdown \
  --confidence_weighted \
  --report_all_variants \
  --require_clean_real_backend \
  --prefer_real_flow_backend \
  --feature_backend dinov2
```

## Aggregate Scores

- Clean GT avg reward: `0.9996457055610642`
- Fast rollout avg reward: `0.7489099937650526`
- Clean > Fast win rate: `1.0`
- Clean GT confidence-weighted avg: `0.982798850450035`
- Fast confidence-weighted avg: `0.4563076715854179`
- Clean > Fast confidence-weighted win rate: `1.0`
- Clean GT real-backend-only avg: `1.0`
- Fast real-backend-only avg: `0.7112765284109178`
- Clean GT flow+DINO-only avg: `1.0`
- Fast flow+DINO-only avg: `0.7112765284109178`

## Backend Coverage

Clean GT:

- Real components: `bg`, `cam`, `fg`, `phys`, `reobs`, `freeze`
- Fallback components: `quality`
- Clean metadata coverage: depth, ID mask, camera, intrinsics, and object-state metadata are present.

Fast rollout:

- Real components: `bg`, `cam`, `fg`, `reobs`
- Fallback components: `phys`, `quality`, `freeze`
- Real RAFT flow contributes to bg/cam.
- Real DINOv2 contributes to fg/reobs.
- Generated depth and generated object masks are still absent.

## Conclusion

Reward v5 is materially stronger than v4: clean > Fast remains 3/3 while both real RAFT flow and real DINO features are active on the Fast side. It is still not fully DPO-ready because physics and generated-mask/depth terms remain proxy/fallback, but it is close enough that the next round can reasonably consider VideoGPA encode smoke if no new camera-condition concern appears.
