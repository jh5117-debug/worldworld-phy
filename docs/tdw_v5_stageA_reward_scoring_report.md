# TDW v5 Stage A Reward Scoring Report

Date: 2026-06-10

Status: blocked pending rollout videos.

Added wrapper:

`cam_physgeo/rewards/score_rollouts.py`

It scores:

- clean GT target video;
- base LingBot-Fast rollout;
- Stage A adapter rollout.

It records:

- `reward_total_confidence_weighted`;
- real-backend confidence;
- fallback/proxy coverage;
- adapter > base count;
- whether generated-video reward is trustworthy enough for pair construction.

No reward calibration was run.

Pair construction must stay blocked until rollout videos exist and reward confidence is sufficient.
