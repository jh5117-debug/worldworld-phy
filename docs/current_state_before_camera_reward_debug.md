# Current State Before Camera / Reward Debug

## Source Reports Read

- `docs/final_report_fast_rollout_reward_10h_autoloop.md`
- `docs/camera_condition_ablation_report.md`
- `docs/reward_feature_backend_after_fast_rollout_report.md`
- `docs/intrinsics_conversion_audit_and_fix.md`
- `docs/github_push_report_fast_rollout_reward_autoloop.md`
- `docs/stage2_videogpa_dpo_plan.md`

## Current State

- Fast rollout count: 3 generated videos.
- Camera ablation: completed for `correct`, `frozen`, and `reversed` on one sample.
- Visual result: the correct/frozen/reversed contact sheet looks very similar, so camera use is not proven.
- Reward-on-rollout clean average: `0.5949`.
- Reward-on-rollout Fast average: `0.8796`.
- Clean > Fast win rate: `0.0`.
- Feature/reward backends: DINOv2 is missing, V-JEPA/VideoMAE is path-only, optical flow is not wired, so rewards are proxy/fallback.
- VideoGPA encode: not allowed.
- DPO: not allowed.

## Priority

Both Gate C and Gate D need work before any VideoGPA/DPO step. The camera path must be audited first because a reward over camera-conditioned rollouts is not meaningful if the model is only using image+prompt. The reward aggregation must also be fixed so fallback or missing backends cannot produce high-confidence high scores.
