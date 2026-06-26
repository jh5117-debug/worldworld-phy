# Prefix-5 DPO Pair Visual Audit Summary

## Result

- old_pair_count: 50
- prefix5_pair_count: 50
- valid_pair_count: 50
- can_enter_dpo_probe_after_real_backend: yes

## Corruption Type Distribution

- background_drift: 8
- nonrigid_background_warp: 7
- object_deformation: 7
- object_identity_change: 7
- wrong_camera_motion: 7
- reobserve_mismatch: 7
- freeze_foreground: 7

## Invalid Reason Stats

- none

## Prefix Verification

All rebuilt pairs set:

- `condition.prefix_len = 5`
- `condition.prediction_start_frame = 5`
- `loss_frame_indices = [5..80]`
- `reward_frame_indices = [5..80]`
- `same_prefix = true`
- `same_prompt = true`
- `same_poses = true`
- `same_intrinsics = true`

The prefix clip contains frames 0-4. Winner and loser futures contain frames 5-80.

## Paths

- manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- audit_csv: `reports/dpo_prefix5_pair_visual_audit/pair_audit.csv`
- audit_jsonl: `reports/dpo_prefix5_pair_visual_audit/pair_audit.jsonl`
- contact_sheet_dir: `reports/dpo_prefix5_pair_visual_audit/pair_contact_sheets`

## DPO Decision

These pairs satisfy the prefix5 schema. DPO still cannot proceed until the real LingBot-Fast winner/loser energy backend is callable and BF16 DDP preflight passes on that real backend.
