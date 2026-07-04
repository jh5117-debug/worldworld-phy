Current Status: PASS

# DPO v12 Subset Summary

## S0_scope_probe_16

- Count: 16
- Path: `manifests/dpo_v12_subsets/s0_scope_probe_16.jsonl`
- Sources: `{'rollout_derived': 8, 'synthetic_controlled': 8}`
- Failure buckets: `{'physical_event_failure': 7, 'identity_change': 3, 'background_drift': 2, 'wrong_camera': 1, 'object_deformation': 1, 'reobserve_mismatch': 1, 'partial_freeze': 1}`
- Templates: `{'containment': 6, 'roll': 4, 'drop': 2, 'collision': 4}`
- Camera motions: `{'orbit_left_44': 6, 'orbit_right_60': 4, 'orbit_left_72': 2, 'orbit_right_64': 4}`
- Conditions: 16
- LocalDPO readiness: `{'GLOBAL_OR_UNKNOWN': 8, 'LOCALDPO_SPATIOTEMPORAL': 8}`

## S1_tiny_dpo_32

- Count: 32
- Path: `manifests/dpo_v12_subsets/s1_tiny_dpo_32.jsonl`
- Sources: `{'rollout_derived': 8, 'synthetic_controlled': 24}`
- Failure buckets: `{'physical_event_failure': 9, 'identity_change': 5, 'background_drift': 4, 'wrong_camera': 3, 'object_deformation': 3, 'reobserve_mismatch': 3, 'partial_freeze': 3, 'other': 2}`
- Templates: `{'containment': 11, 'roll': 8, 'drop': 3, 'collision': 10}`
- Camera motions: `{'orbit_left_44': 11, 'orbit_right_60': 8, 'orbit_left_72': 3, 'orbit_right_64': 9, 'strafe_left_180': 1}`
- Conditions: 32
- LocalDPO readiness: `{'GLOBAL_OR_UNKNOWN': 8, 'LOCALDPO_SPATIOTEMPORAL': 24}`

## S2_small_dpo_64

- Count: 64
- Path: `manifests/dpo_v12_subsets/s2_small_dpo_64.jsonl`
- Sources: `{'rollout_derived': 15, 'synthetic_controlled': 49}`
- Failure buckets: `{'physical_event_failure': 16, 'identity_change': 12, 'background_drift': 7, 'wrong_camera': 6, 'object_deformation': 6, 'reobserve_mismatch': 6, 'partial_freeze': 6, 'other': 5}`
- Templates: `{'containment': 19, 'roll': 15, 'drop': 11, 'collision': 19}`
- Camera motions: `{'orbit_left_44': 19, 'orbit_right_60': 15, 'orbit_left_72': 11, 'orbit_right_64': 14, 'strafe_left_180': 5}`
- Conditions: 64
- LocalDPO readiness: `{'GLOBAL_OR_UNKNOWN': 15, 'LOCALDPO_SPATIOTEMPORAL': 49}`

## S3_dpo_128_optional

- Count: 128
- Path: `manifests/dpo_v12_subsets/s3_dpo_128_optional.jsonl`
- Sources: `{'rollout_derived': 15, 'synthetic_controlled': 113}`
- Failure buckets: `{'physical_event_failure': 24, 'identity_change': 20, 'background_drift': 15, 'wrong_camera': 14, 'object_deformation': 14, 'reobserve_mismatch': 14, 'partial_freeze': 14, 'other': 13}`
- Templates: `{'containment': 36, 'roll': 30, 'drop': 25, 'collision': 37}`
- Camera motions: `{'orbit_left_44': 36, 'orbit_right_60': 30, 'orbit_left_72': 25, 'orbit_right_64': 28, 'strafe_left_180': 9}`
- Conditions: 89
- LocalDPO readiness: `{'GLOBAL_OR_UNKNOWN': 15, 'LOCALDPO_SPATIOTEMPORAL': 113}`

## val_energy_16

- Count: 16
- Path: `manifests/dpo_v12_subsets/val_energy_16.jsonl`
- Sources: `{'synthetic_controlled': 16}`
- Failure buckets: `{'identity_change': 6, 'partial_freeze': 5, 'physical_event_failure': 1, 'other': 4}`
- Templates: `{'containment': 8, 'drop': 1, 'collision': 7}`
- Camera motions: `{'orbit_left_44': 8, 'orbit_left_72': 1, 'orbit_right_64': 6, 'strafe_left_180': 1}`
- Conditions: 16
- LocalDPO readiness: `{'LOCALDPO_SPATIOTEMPORAL': 16}`

## val_video_16

- Count: 16
- Path: `manifests/dpo_v12_subsets/val_video_16.jsonl`
- Sources: `{'rollout_derived': 8, 'synthetic_controlled': 8}`
- Failure buckets: `{'physical_event_failure': 7, 'identity_change': 4, 'background_drift': 2, 'wrong_camera': 1, 'object_deformation': 1, 'partial_freeze': 1}`
- Templates: `{'containment': 4, 'roll': 4, 'drop': 3, 'collision': 5}`
- Camera motions: `{'orbit_left_44': 4, 'orbit_right_60': 4, 'orbit_left_72': 3, 'orbit_right_64': 5}`
- Conditions: 16
- LocalDPO readiness: `{'GLOBAL_OR_UNKNOWN': 8, 'LOCALDPO_SPATIOTEMPORAL': 8}`

## Caveat

The repaired canonical pool is dominated by controlled synthetic pairs. Rollout-derived rows are included in scope/video sanity subsets where available, but real rollout-derived DPO remains limited.
