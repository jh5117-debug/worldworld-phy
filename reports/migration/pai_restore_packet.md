# PhysEditWorld PAI Restore Packet

Generated UTC: `2026-07-09T02:23:29.483588+00:00`
Decision: `PAI_RESTORE_PACKET_BLOCKED_NAS_OR_ROOT`

## Git

- repo: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys`
- branch: `physion-only-local-assets-videogpa-smoke`
- local head: `7a76645`
- origin branch head: `d162939`

## Current Blockers

- `NAS_TARGET_MISSING`
- `PHYS_EDITWORLD_ROOTS_MISSING_OR_INVALID`
- `BACKEND_NOT_READY:PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY`
- `REQUIREMENT_MATRIX_NOT_PASS:PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS`
- `OBJECTIVE_NOT_COMPLETE:PHYS_EDITWORLD_OBJECTIVE_INCOMPLETE_AT_PHASE0_MIGRATION`

## NAS And Root

- NAS target `/mnt/workspace/hj/nas_hj`: `missing`
- `PHYS_EDITWORLD_ROOTS`: `UNSET`
- no root candidates supplied via `PHYS_EDITWORLD_ROOTS`

## Decisions

- `pai_handoff`: `PAI_HANDOFF_BLOCKED_NAS_OR_ROOT` (`reports/migration/pai_handoff_status.json`)
- `phase0_preflight`: `PHYS_EDITWORLD_PHASE0_BLOCKED_AT_ROOT_CANDIDATES` (`reports/migration/phase0_preflight_status.json`)
- `root_candidates`: `PHYS_EDITWORLD_ROOT_CANDIDATES_NONE_STRONG` (`reports/migration/physeditworld_root_candidates_ranked.json`)
- `root_submission_template`: `PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY` (`reports/migration/physeditworld_root_submission_template.json`)
- `root_submission_validation`: `PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE` (`reports/migration/physeditworld_root_submission_validation.json`)
- `root_evidence_samples`: `PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE` (`reports/migration/physeditworld_root_evidence_samples.json`)
- `root_onboarding_sequence`: `PHYS_EDITWORLD_ROOT_ONBOARDING_WAITING_FOR_FILLED_TEMPLATE` (`reports/migration/physeditworld_root_onboarding_sequence.json`)
- `root_schema_probe`: `PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT` (`reports/migration/physeditworld_root_schema_probe.json`)
- `root_selection`: `PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT` (`reports/migration/physeditworld_selected_root_status.json`)
- `root_intake`: `PHYS_EDITWORLD_ROOT_INTAKE_WAITING_FOR_EXTERNAL_ROOT` (`reports/migration/physeditworld_root_intake.json`)
- `locked_handoff`: `LOCKED_HANDOFF_BLOCKED_AT_ROOT_SCHEMA_PROBE` (`reports/migration/locked_handoff_sequence.json`)
- `migration_asset_validation`: `MIGRATION_ASSET_VALIDATION_NAS_BLOCKED` (`reports/migration/migration_asset_validation.json`)
- `approved_copy`: `APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS` (`reports/migration/approved_copy_status.json`)
- `migration_size_summary`: `MIGRATION_SIZE_SUMMARY_NO_APPROVED_ROWS` (`reports/migration/migration_size_summary.json`)
- `migration_approval_review`: `MIGRATION_APPROVAL_REVIEW_PACKET_READY` (`reports/migration/migration_approval_review_packet.json`)
- `backend_readiness`: `PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY` (`reports/physeditworld_50h/backend_readiness/backend_readiness.json`)
- `pipeline_gate`: `PIPELINE_BLOCKED_AT_ROOT_SCHEMA_PROBE` (`reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json`)
- `requirement_matrix`: `PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS` (`reports/physeditworld_50h/requirement_matrix.json`)
- `completion_audit`: `PHYS_EDITWORLD_OBJECTIVE_INCOMPLETE_AT_PHASE0_MIGRATION` (`reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json`)

## Migration Size Snapshot

- decision: `MIGRATION_SIZE_SUMMARY_NO_APPROVED_ROWS`
- candidate rows: `800`
- candidate present file bytes: `6415095518` (5.97 GB)
- directory rows pending recursive sizing: `237`
- candidate missing rows: `2`
- approved-copy decision: `APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS`
- approved rows: `0`
- approved present file bytes: `0`

## Manifest Rows

- `manifests/physeditworld_50h_all.jsonl`: `EMPTY` rows=0
- `manifests/physeditworld_50h_train.jsonl`: `EMPTY` rows=0
- `manifests/physeditworld_50h_val.jsonl`: `EMPTY` rows=0
- `manifests/physeditworld_50h_test.jsonl`: `EMPTY` rows=0
- `manifests/physeditworld_50h_lingbot_train.jsonl`: `EMPTY` rows=0
- `manifests/physeditworld_50h_lingbot_val.jsonl`: `EMPTY` rows=0
- `manifests/physeditworld_dpo_pairs_anchored_v0.jsonl`: `EMPTY` rows=0

## Restore Entrypoints

- `scripts/migration/bootstrap_pai_physeditworld.sh`: `exists`
- `scripts/migration/run_physeditworld_pai_restore_packet.sh`: `exists`
- `docs/physeditworld_50h_pai_bootstrap.md`: `exists`

## Safe Next Commands

```bash
export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root
```
```bash
bash scripts/migration/write_physeditworld_root_submission_template.sh
```
```bash
bash scripts/migration/validate_physeditworld_root_submission.sh
```
```bash
bash scripts/migration/sample_physeditworld_root_evidence.sh
```
```bash
bash scripts/migration/run_physeditworld_root_onboarding_sequence.sh
```
```bash
bash scripts/migration/bootstrap_pai_physeditworld.sh
```
```bash
bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh
```
```bash
bash scripts/migration/write_physeditworld_external_unblock_packet.sh
```
```bash
bash scripts/migration/verify_pai_physeditworld_handoff.sh
```
```bash
bash scripts/migration/run_physeditworld_phase0_preflight.sh
```
```bash
python3 -m cam_physgeo.orchestration.physeditworld_backend_readiness
```
```bash
bash scripts/run_physeditworld_pipeline_gates.sh
```
```bash
python3 -m cam_physgeo.orchestration.physeditworld_requirement_matrix
```
```bash
bash scripts/migration/run_physeditworld_completion_audit.sh
```
```bash
bash scripts/migration/run_physeditworld_pai_restore_packet.sh
```

## Safety

This packet is CPU/IO only. It does not copy files, delete files, use GPUs, train, rollout, run DPO, or push large artifacts.
