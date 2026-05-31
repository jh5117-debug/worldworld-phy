# Reward On Fast Rollout Debug V3 Report

## Command

```bash
CUDA_VISIBLE_DEVICES=6,7 python -m cam_physgeo.eval.eval_fast_rollouts \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --rollouts local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke \
  --out local_assets/reports/reward_calibration/fast_zero_shot_reward_debug_v3 \
  --limit 3 \
  --save_debug \
  --gpu_ids 6,7 \
  --debug_reward_breakdown \
  --confidence_weighted \
  --report_all_variants \
  --require_clean_real_backend
```

## Summary

- Valid pairs: `3`
- Raw clean avg: `0.9996`
- Raw Fast avg: `0.8796`
- Raw clean > Fast win rate: `1.0`
- Confidence-weighted clean avg: `0.9828`
- Confidence-weighted Fast avg: `0.2175`
- Confidence-weighted clean > Fast win rate: `1.0`
- Clean real-backend-only avg: `1.0`
- Fast real-backend-only avg: `0.0`

## Backend Coverage

Clean GT:

- Real components: `bg`, `cam`, `fg`, `phys`, `reobs`, `freeze`
- Fallback component: `quality`
- Missing components: none for the processed clean assets.

Fast rollout:

- Real components: none.
- Fallback components: `bg`, `cam`, `fg`, `phys`, `reobs`, `quality`, `freeze`
- Missing generated depth/id/learned feature/learned flow.

## Interpretation

The previous reversed reward behavior was caused by proxy/fallback components being allowed to dominate. V3 fixes the aggregation issue by marking clean Physion metadata as real and keeping Fast rollout proxy components low confidence.

This is still not DPO-ready. The clean side is now trustworthy enough for smoke diagnostics, but Fast rollout scoring still needs real generated-video feature and flow backends before it can be used for pair selection.
