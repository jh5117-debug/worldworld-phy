# Prior Art: Reward v5 Rollout Scoring Review

Date: 2026-06-10

Existing reward entrypoint:

`cam_physgeo/rewards/score_rollouts.py`

Existing pair builder:

`cam_physgeo/dpo/build_reward_pairs.py`

Reward implementation:

- `cam_physgeo/rewards/total_reward.py` aggregates `R_bg`, `R_cam`, `R_fg`, `R_phys`, `R_reobs`, `R_quality`, and `P_freeze`.
- Reward v5 already reports confidence-weighted, real-backend-only, proxy-only, and flow/DINO-only totals.
- `cam_physgeo/rewards/flow_backend.py` provides local RAFT-backed optical flow when the copied RAFT repo and checkpoint are present.
- `cam_physgeo/rewards/feature_backend.py` provides DINOv2-small feature extraction from local weights.
- Confidence handling marks real, fallback, and missing components explicitly.

Wrapper update in this pass:

- `score_rollouts.py` now accepts the planned CLI flags for scoring GT, base, and adapter videos.
- It attaches existing RAFT and DINO backend results into `score_sample()` when requested.
- It writes `scores.jsonl`, `reward_summary.csv`, `reward_breakdown_by_condition.csv`, and `reward_backend_coverage.json`.
- Reward weights are not changed.

Pair construction rule:

`build_reward_pairs.py` only constructs diagnostic pair manifests after margin and confidence thresholds pass. It does not run DPO.
