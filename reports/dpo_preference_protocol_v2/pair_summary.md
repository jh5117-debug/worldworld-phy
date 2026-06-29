# DPO Preference Protocol v2 Pair Summary

Current Status: MIXED_TYPEA_READY_TYPEB_BLOCKED_BY_BLUR

- Final manifest: `manifests/dpo_preference_protocol_v2_pairs.jsonl`
- Total pairs: 34
- Type A local corruption pairs: 34
- Type B rollout pairs passing v2 sharpness gate: 0
- Type B v1 candidates rejected by v2 gate: 16 / 16

## Type B Decision

Type B rollout losers are not used in protocol v2 unless they pass the sharpness-aware gate. The current selected v1 Type B losers fail primarily on `loser_sharpness_ratio < 0.55`, so v2 falls back to Type A local corruption pairs for stable DPO engineering run-through input.

## Rejection Reasons

- sharpness_ratio_lt_0.55: 16
- r_quality_below_condition_p40: 10

## Safety

No training, DPO scaling, StageB, GRPO, checkpoint deletion, or data/weight/video push was performed while building protocol v2.
