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
