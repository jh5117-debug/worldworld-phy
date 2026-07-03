Current Status: PASS

# DPO Pair Factory v10b Final Audit Report

Generated: 2026-07-03 22:16:34

## Summary

DPO Pair Factory v10b freezes the v10 preference-pair output as a documented data asset. The final ready manifest contains 81 pairs, with 81 strict-ready/trainable pairs, 0 diagnostic-only pairs, and 0 rejected pairs after schema/source/visual-gate audit.

Source breakdown:

- Real rollout-derived GT>C pairs: 15
- Controlled synthetic TypeM-v10 pairs: 63
- Human-visible TypeA_plus controlled pairs: 3

Important caveat: the 63 TypeM-v10 pairs are controlled synthetic visible negatives, not real model rollout losers. They are useful for anchored/LocalDPO-style controlled objectives, but they are not evidence that real rollout loser mining is solved.

## Audit Result

- Strict ready: 81
- Trainable: 81
- Diagnostic-only: 0
- Rejected: 0
- LocalDPO/time-mask ready pairs: see subset summary below; controlled pairs carry affected-region/time-span metadata.

## Subsets

- All strict ready: `manifests/dpo_pair_factory_v10b_ready_all.jsonl` (81)
- Rollout-only: `manifests/dpo_pair_factory_v10b_ready_rollout_only.jsonl` (15)
- Synthetic controlled only: `manifests/dpo_pair_factory_v10b_ready_synthetic_controlled.jsonl` (66)
- Top50 balanced: `manifests/dpo_pair_factory_v10b_top50_balanced.jsonl` (50)
- Top20 demo: `manifests/dpo_pair_factory_v10b_top20_demo.jsonl` (20)
- PPT subset: `manifests/dpo_pair_factory_v10b_ppt_subset.jsonl` (5)

## Synthetic Quality

- Synthetic total: 63
- Synthetic trainable: 63
- Synthetic diagnostic-only: 0
- Synthetic rejected: 0
- Caveat: controlled synthetic, not rollout-derived.

## Rollout Quality

- Rollout total: 15
- Rollout trainable: 15
- Rollout diagnostic-only: 0
- Rollout rejected: 0
- Caveat: real rollout-derived subset remains small and must be expanded before claiming a real rollout pair factory.

## Decision

Pair-data gate for anchored tiny DPO: PASS. The top50 balanced subset is enough for a controlled anchored tiny DPO experiment once the winner-side objective path is validated.

Real rollout DPO gate: NOT READY. The rollout-only subset has 15 trainable pairs, which is useful for analysis and demos but not enough to claim robust model-distribution DPO data.

No training, DPO, SDPO, Linear-DPO, winner-anchor, StageA, StageB, GRPO, or broad-LoRA was run in v10b.

## Detailed Subset Summary

Current Status:
SUBSETS_READY

# DPO Pair Factory v10b Subset Summary

## all_ready
- Count: 81
- Templates: `{"collision": 26, "containment": 32, "drop": 19, "roll": 4}`
- Failure tags: `{"collision_event_failure": 1, "collision_extra_objects": 1, "containment_extra_objects": 2, "containment_failure": 3, "event_extra_objects": 1, "event_missing_or_fragments": 1, "foreground_identity_color_shift": 20, "foreground_identity_event": 1, "foreground_identity_extra_objects": 2, "local_patch_drift": 16, "local_patch_freeze": 14, "local_temporal_jump": 13, "object_identity_change_local": 1, "partial_freeze": 2, "physical_event_fragments": 1, "roll_identity_event": 2}`
- Pair types: `{"GT_C": 15, "TypeA_plus": 3, "TypeM_v10_synthetic_visible": 63}`
- LocalDPO-ready: 66
- Time-mask ready: 66
- Diagnostic-only: 0

## rollout_only
- Count: 15
- Templates: `{"collision": 2, "containment": 6, "drop": 3, "roll": 4}`
- Failure tags: `{"collision_event_failure": 1, "collision_extra_objects": 1, "containment_extra_objects": 2, "containment_failure": 3, "event_extra_objects": 1, "event_missing_or_fragments": 1, "foreground_identity_event": 1, "foreground_identity_extra_objects": 2, "physical_event_fragments": 1, "roll_identity_event": 2}`
- Pair types: `{"GT_C": 15}`
- LocalDPO-ready: 0
- Time-mask ready: 0
- Diagnostic-only: 0

## synthetic_controlled
- Count: 66
- Templates: `{"collision": 24, "containment": 26, "drop": 16}`
- Failure tags: `{"foreground_identity_color_shift": 20, "local_patch_drift": 16, "local_patch_freeze": 14, "local_temporal_jump": 13, "object_identity_change_local": 1, "partial_freeze": 2}`
- Pair types: `{"TypeA_plus": 3, "TypeM_v10_synthetic_visible": 63}`
- LocalDPO-ready: 66
- Time-mask ready: 66
- Diagnostic-only: 0

## top50_balanced
- Count: 50
- Templates: `{"collision": 23, "containment": 20, "drop": 3, "roll": 4}`
- Failure tags: `{"collision_event_failure": 1, "collision_extra_objects": 1, "containment_extra_objects": 2, "containment_failure": 3, "event_extra_objects": 1, "event_missing_or_fragments": 1, "foreground_identity_color_shift": 8, "foreground_identity_event": 1, "foreground_identity_extra_objects": 2, "local_patch_drift": 8, "local_patch_freeze": 8, "local_temporal_jump": 8, "object_identity_change_local": 1, "partial_freeze": 2, "physical_event_fragments": 1, "roll_identity_event": 2}`
- Pair types: `{"GT_C": 15, "TypeA_plus": 3, "TypeM_v10_synthetic_visible": 32}`
- LocalDPO-ready: 35
- Time-mask ready: 35
- Diagnostic-only: 0

## top20_demo
- Count: 20
- Templates: `{"collision": 14, "containment": 3, "drop": 1, "roll": 2}`
- Failure tags: `{"containment_failure": 2, "event_extra_objects": 1, "event_missing_or_fragments": 1, "foreground_identity_color_shift": 3, "local_patch_drift": 3, "local_patch_freeze": 3, "local_temporal_jump": 3, "object_identity_change_local": 1, "partial_freeze": 2, "physical_event_fragments": 1}`
- Pair types: `{"GT_C": 5, "TypeA_plus": 3, "TypeM_v10_synthetic_visible": 12}`
- LocalDPO-ready: 15
- Time-mask ready: 15
- Diagnostic-only: 0

## ppt_subset
- Count: 5
- Templates: `{"containment": 1, "drop": 4}`
- Failure tags: `{"foreground_identity_color_shift": 1, "foreground_identity_extra_objects": 1, "local_patch_drift": 1, "local_patch_freeze": 1, "local_temporal_jump": 1}`
- Pair types: `{"GT_C": 1, "TypeM_v10_synthetic_visible": 4}`
- LocalDPO-ready: 4
- Time-mask ready: 4
- Diagnostic-only: 0

