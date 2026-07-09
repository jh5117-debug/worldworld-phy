# PhysEditWorld External Unblock Packet

Generated UTC: `2026-07-09T02:03:14.222844+00:00`
Decision: `PHYS_EDITWORLD_EXTERNAL_UNBLOCK_REQUIRED_NAS_OR_ROOT`

## Blockers

- `NAS_TARGET_MISSING`
- `PHYS_EDITWORLD_ROOTS_UNSET`
- `NO_STRONG_ROOT_CANDIDATE_VISIBLE`
- `ROOT_SCHEMA_PROBE_WAITING_FOR_ROOT`
- `BACKEND_NOT_READY:PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY`

## Required Root Evidence

- `video_or_frames`
- `action_trace`
- `camera_trajectory_or_poses`
- `intrinsics`
- `gravity_label_or_metadata`
- `replay_group_or_matched_replay_metadata`

## NAS And Root Visibility

- NAS target `/mnt/workspace/hj/nas_hj`: `missing`
- `PHYS_EDITWORLD_ROOTS`: `UNSET`

## Migration Size Snapshot

- decision: `MIGRATION_SIZE_SUMMARY_NO_APPROVED_ROWS`
- candidate present file bytes: `5.97 GB`
- candidate rows: `800`
- directory rows pending recursive sizing: `237`
- approved rows: `0`
- approved present file bytes: `0`

## Decision Snapshot

- `root_candidates`: `PHYS_EDITWORLD_ROOT_CANDIDATES_NONE_STRONG` (`reports/migration/physeditworld_root_candidates_ranked.json`)
- `root_submission_template`: `PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY` (`reports/migration/physeditworld_root_submission_template.json`)
- `root_submission_validation`: `PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE` (`reports/migration/physeditworld_root_submission_validation.json`)
- `root_schema_probe`: `PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT` (`reports/migration/physeditworld_root_schema_probe.json`)
- `root_selection`: `PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT` (`reports/migration/physeditworld_selected_root_status.json`)
- `root_intake`: `PHYS_EDITWORLD_ROOT_INTAKE_WAITING_FOR_EXTERNAL_ROOT` (`reports/migration/physeditworld_root_intake.json`)
- `phase0_preflight`: `PHYS_EDITWORLD_PHASE0_BLOCKED_AT_ROOT_CANDIDATES` (`reports/migration/phase0_preflight_status.json`)
- `pai_handoff`: `PAI_HANDOFF_BLOCKED_NAS_OR_ROOT` (`reports/migration/pai_handoff_status.json`)
- `pai_restore_packet`: `PAI_RESTORE_PACKET_BLOCKED_NAS_OR_ROOT` (`reports/migration/pai_restore_packet.json`)
- `migration_size_summary`: `MIGRATION_SIZE_SUMMARY_NO_APPROVED_ROWS` (`reports/migration/migration_size_summary.json`)
- `migration_approval_review`: `MIGRATION_APPROVAL_REVIEW_PACKET_READY` (`reports/migration/migration_approval_review_packet.json`)
- `backend_readiness`: `PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY` (`reports/physeditworld_50h/backend_readiness/backend_readiness.json`)
- `requirement_matrix`: `PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS` (`reports/physeditworld_50h/requirement_matrix.json`)
- `completion_audit`: `PHYS_EDITWORLD_OBJECTIVE_INCOMPLETE_AT_PHASE0_MIGRATION` (`reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json`)

## Post-Mount Commands

```bash
export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root
bash scripts/migration/write_physeditworld_root_submission_template.sh
bash scripts/migration/validate_physeditworld_root_submission.sh
bash scripts/migration/select_physeditworld_root.sh
bash scripts/migration/probe_physeditworld_root_schema.sh
bash scripts/migration/prepare_physeditworld_root_intake.sh
bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh
bash scripts/migration/run_physeditworld_phase0_preflight.sh
python3 -m cam_physgeo.orchestration.physeditworld_backend_readiness
bash scripts/run_physeditworld_pipeline_gates.sh
python3 -m cam_physgeo.orchestration.physeditworld_requirement_matrix
bash scripts/migration/run_physeditworld_completion_audit.sh
bash scripts/migration/run_physeditworld_pai_restore_packet.sh
bash scripts/migration/verify_pai_physeditworld_handoff.sh
bash scripts/migration/run_physeditworld_pai_restore_packet.sh
```

## Safety

This packet is CPU/IO only. It does not copy files, delete files, use GPUs, train, rollout, run DPO, or execute rsync.
