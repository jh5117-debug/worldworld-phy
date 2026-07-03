Current Status: MIXED

# Ready500 Loser Quality Audit

- Audited pairs: 500
- Trainable after loser audit: 497
- Reject/review: 3
- Status counts: `{'TRAINABLE': 497, 'REJECT_OR_REVIEW': 3}`
- Source counts: `{'rollout_derived': 15, 'TypeA_plus': 3, 'synthetic_controlled': 482}`
- Failure counts: `{'event_extra_objects': 1, 'event_missing_or_fragments': 1, 'physical_event_fragments': 1, 'containment_failure': 3, 'foreground_identity_event': 1, 'foreground_identity_extra_objects': 2, 'collision_event_failure': 1, 'collision_extra_objects': 1, 'roll_identity_event': 2, 'containment_extra_objects': 2, 'object_identity_change_local': 1, 'partial_freeze': 2, 'background_drift_visible': 36, 'collision_response_failure_synthetic': 59, 'containment_failure_synthetic': 48, 'drop_motion_failure_synthetic': 17, 'foreground_identity_color_shift': 20, 'local_patch_drift': 16, 'local_patch_freeze': 14, 'local_scene_patch_drift': 42, 'local_temporal_jump': 13, 'object_deformation_visible': 15, 'object_duplicate_or_fragment': 19, 'object_identity_color_shift': 46, 'partial_freeze_foreground': 51, 'reobserve_mismatch_visible': 46, 'roll_event_fragment_synthetic': 16, 'wrong_camera_motion_visible': 24}`
- Reject reasons: `{'too_subtle_metric': 3}`
- Trainable manifest: `manifests/dpo_pair_factory_v11_ready500_trainable_after_loser_audit.jsonl`

Decision: only rows with `trainable_after_loser_audit=True` should be used for training. Rows marked `REJECT_OR_REVIEW` require manual correction or exclusion.
