# DPO Preference Protocol v1 Pair Summary

## Counts

- total_pair_count: 66
- valid_pair_count: 66
- pair_audit_csv: `reports/dpo_preference_protocol_v1/pair_audit.csv`
- pair_contact_sheet_dir: `reports/dpo_preference_protocol_v1/pair_contact_sheets`

## Pair Type Distribution

- local_corruption: 50
- gt_vs_medium_hard_rollout: 16

## Corruption / Failure Distribution

- background_drift_local: 8
- wrong_camera_motion_local: 7
- object_deformation_local: 7
- object_identity_change_local: 7
- reobserve_mismatch_local: 7
- partial_freeze: 7
- physical_event_local_failure: 7
- event_missing;object_duplicate;object_identity_change: 10
- event_missing;object_duplicate;object_identity_change;physical_event_failure;wrong_camera_motion: 6

## Energy Audit

- real_energy_sampled_count: 5
- proxy_energy_count: 61
- full_energy_audit_status: PARTIAL_REAL_SAMPLE_PLUS_PROXY_TRIAGE

## Decision

Protocol v1 is ready as a preference-pair generation protocol if the downstream DPO run first uses Type A local-corruption pairs and performs full real-energy audit on the selected training subset. It is not a DPO training result.
