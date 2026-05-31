# Reward On Fast Rollout Debug V4 Report

## Run

- Command target: `cam_physgeo.eval.eval_fast_rollouts`
- Samples: `local_assets/data/physion/processed/lingbot_cam_inputs/smoke`
- Rollouts: `local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke`
- Output: `local_assets/reports/reward_calibration/fast_zero_shot_reward_debug_v4`
- Limit: `3`
- Flags: `--require_clean_real_backend --prefer_real_flow_backend --confidence_weighted --report_all_variants`

## Aggregate Scores

- Clean GT avg reward: `0.9996457055610642`
- Fast rollout avg reward: `0.7617640182184134`
- Clean > Fast win rate: `1.0`
- Clean GT confidence-weighted avg: `0.982798850450035`
- Fast confidence-weighted avg: `0.28148399796357515`
- Clean > Fast confidence-weighted win rate: `1.0`
- Clean GT real-backend-only avg: `1.0`
- Fast real-backend-only avg: `0.47644271948215194`
- Clean GT proxy-only avg: `0.9819309836142694`
- Fast proxy-only avg: `0.9454482759226299`

## Backend Coverage

Clean GT rows:

- Real components: `bg`, `cam`, `fg`, `phys`, `reobs`, `freeze`
- Fallback components: `quality`
- Metadata coverage: depth, ID mask, camera, intrinsics, and object-state metadata are present.

Fast rollout rows:

- Real components: `bg`, `cam`
- Fallback components: `fg`, `phys`, `reobs`, `quality`, `freeze`
- Flow available only: about `0.47-0.49` across the three samples.
- Feature available only: `0.0`

The generated report's pair-level coverage shows real RAFT flow is used for Fast-side bg/cam. A stale template sentence in an earlier summary said optical flow was not used; code was updated so future summaries report this dynamically.

## Interpretation

Reward v4 keeps the clean > Fast ordering after adding real RAFT flow for the generated rollout side. The score is still not DPO-ready because Fast-side identity/reobserve terms still depend on proxy visual signatures rather than real DINO/V-JEPA features, and generated depth is still absent. The correct next reward step is DINOv2-small forward, not VideoGPA or DPO.
