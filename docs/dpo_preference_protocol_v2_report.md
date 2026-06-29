# DPO Preference Protocol v2 Report

Current Status: MIXED_TYPEA_READY_TYPEB_BLOCKED_BY_BLUR
Updated: 2026-06-29 14:18:28

## Summary

- Final manifest: `manifests/dpo_preference_protocol_v2_pairs.jsonl`
- Total valid v2 pairs: 34
- Type A local corruption pairs: 34
- Type B medium-hard rollout pairs: 0
- Type C pairs: 0
- Type B v1 candidates audited: 16
- Type B rejected by v2: 16

## Why Type B Was Blocked

The stricter quality gate rejected all v1 Type B rollout losers. The dominant reason was sharpness: every audited Type B loser failed `loser_sharpness_ratio >= 0.55`. Several also failed the per-condition R_quality p40 threshold. These videos should not be used as DPO losers because blur would become the preference signal instead of physics/camera/world consistency.

Reject reason distribution:

```json
{
  "r_quality_below_condition_p40": 10,
  "sharpness_ratio_lt_0.55": 16
}
```

## Current Usable Data

Protocol v2 is usable for LocalDPO-style / controlled-corruption engineering experiments using Type A pairs. It is not yet a stable rollout-based Type B dataset.

## Next Step

For DPO engineering only: use a tiny Type A subset and require true V2V-5 checkpoint video evaluation. For rollout-based DPO data: first run candidate-generator v2 or improve the rollout quality floor so Type B losers are clear, medium-hard, and not blur-dominated.
