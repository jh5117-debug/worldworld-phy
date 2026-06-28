# Full Real-Energy Audit Summary

Pair manifest: `manifests/dpo_preference_protocol_v1_pairs.jsonl`
Total pairs: 66
Real-energy ok: 66
Real-energy failed/missing: 0
Energy threshold for DPO-ready selection: 0.00334223
DPO-ready pairs: 50
LocalDPO-ready pairs: 34

## Energy Margin By Type

### gt_vs_medium_hard_rollout
- count: 16
- Delta_ref mean/median/min/max: 0.06978276715381071/0.07530556991696358/0.014671958051621914/0.11708655208349228
- positive Delta_ref: 16 / 16
- reward_margin mean/median: 0.3170330959616618/0.30518612452173055

### local_corruption
- count: 50
- Delta_ref mean/median/min/max: 0.010275943037122488/0.009849360212683678/-0.024275071918964386/0.028059273958206177
- positive Delta_ref: 46 / 50
- reward_margin mean/median: 0.21999999999999997/0.21999999999999997

## Selection Rejection Reasons

- weak_or_negative_energy_margin: 11
- capped_by_top_energy_margin: 5

## Training Recommendation

This file is an audit-only artifact: no DPO optimizer step was run.
Use `dpo_ready_pairs.jsonl` only if the ready count is at least 20; otherwise treat the protocol as blocked by weak real-energy margin.
