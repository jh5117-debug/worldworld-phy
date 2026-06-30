# Reward Visual Alignment v5 Summary

Current Status: PROTOCOL_V4_NOT_READY_TOO_SUBTLE

- Total v4 pairs checked: 42
- Human-visible count: 3
- True medium-hard count: 3
- Too subtle count: 39
- TypeA_plus too subtle: 31
- TypeM true medium-hard: 0
- Reward margin / visual score correlation: 0.3278
- Ready JSONL: `reports/reward_visual_alignment_v5/dpo_ready_pairs_visual_v5.jsonl`
- Rejected JSONL: `reports/reward_visual_alignment_v5/rejected_too_subtle_pairs.jsonl`

## Interpretation

The v5 gate is intentionally stricter than v4: positive proxy reward is not enough. A pair must have visible local difference, explainable failure, aligned subreward drop, and non-blurry loser. Pairs that look the same without a heatmap are marked `VISUAL_TOO_SUBTLE` and removed from DPO-ready.

Reward innovation is only partially grounded while reward backend remains proxy/diagnostic. The missing pieces are real perceptual/local LPIPS, real physics subreward backends, and a human-visible local difference gate.
