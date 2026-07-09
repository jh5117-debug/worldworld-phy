# PhysEditWorld PAI Handoff Verification

Decision: `PAI_HANDOFF_BLOCKED_NAS_OR_ROOT`

## Status Counts

- `BLOCKED`: 4
- `PASS`: 5

## Checks

- `git_branch`: `PASS`
  - detail: branch=physion-only-local-assets-videogpa-smoke
- `git_head`: `PASS`
  - detail: 39cc4e0
- `forbidden_staged_files`: `PASS`
  - detail: none
- `required_handoff_files`: `PASS`
  - detail: missing=0 total=44
- `phase0_report_artifacts`: `PASS`
  - detail: missing=0 total=23 decisions={"reports/migration/approved_copy_status.json": "APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS", "reports/migration/locked_handoff_sequence.json": "LOCKED_HANDOFF_BLOCKED_AT_ROOT_SCHEMA_PROBE", "reports/migration/migration_approval_review_packet.json": "MIGRATION_APPROVAL_REVIEW_PACKET_READY", "reports/migration/migration_asset_validation.json": "MIGRATION_ASSET_VALIDATION_NAS_BLOCKED", "reports/migration/migration_size_summary.json": "MIGRATION_SIZE_SUMMARY_NO_APPROVED_ROWS", "reports/migration/pai_restore_packet.json": "PAI_RESTORE_PACKET_BLOCKED_NAS_OR_ROOT", "reports/migration/phase0_preflight_status.json": "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_ROOT_CANDIDATES", "reports/migration/physeditworld_external_unblock_packet.json": "PHYS_EDITWORLD_EXTERNAL_UNBLOCK_REQUIRED_NAS_OR_ROOT", "reports/migration/physeditworld_pai_readiness.json": "PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED", "reports/migration/physeditworld_root_candidates_ranked.json": "PHYS_EDITWORLD_ROOT_CANDIDATES_NONE_STRONG", "reports/migration/physeditworld_root_evidence_samples.json": "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE", "reports/migration/physeditworld_root_intake.json": "PHYS_EDITWORLD_ROOT_INTAKE_WAITING_FOR_EXTERNAL_ROOT", "reports/migration/physeditworld_root_schema_probe.json": "PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT", "reports/migration/physeditworld_root_submission_template.json": "PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY", "reports/migration/physeditworld_root_submission_validation.json": "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE", "reports/migration/physeditworld_selected_root_status.json": "PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT", "reports/physeditworld_50h/backend_readiness/backend_readiness.json": "PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY", "reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json": "PHYS_EDITWORLD_OBJECTIVE_INCOMPLETE_AT_PHASE0_MIGRATION", "reports/physeditworld_50h/manifest_init/empty_manifest_init.json": "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT", "reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json": "PIPELINE_BLOCKED_AT_ROOT_SCHEMA_PROBE", "reports/physeditworld_50h/requirement_matrix.json": "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS"}
- `nas_target`: `BLOCKED` (/mnt/workspace/hj/nas_hj)
  - detail: missing
  - next: mount or expose PAI/NAS target path
- `physeditworld_root_input`: `BLOCKED`
  - detail: PHYS_EDITWORLD_ROOTS not set
  - next: set PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h
- `strict_manifest`: `BLOCKED` (manifests/physeditworld_50h_all.jsonl)
  - detail: rows=0 required>=1
  - next: mount selected root and rerun post-mount continuation
- `lingbot_train_manifest`: `BLOCKED` (manifests/physeditworld_50h_lingbot_train.jsonl)
  - detail: rows=0 required>=1
  - next: mount selected root and rerun post-mount continuation

## Safe Next Commands

```bash
# Preferred one-command path after NAS/root are visible:
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h \
  bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh

# Read-only completion evidence after any handoff run:
python3 -m cam_physgeo.orchestration.physeditworld_backend_readiness
bash scripts/migration/run_physeditworld_completion_audit.sh
bash scripts/migration/run_physeditworld_pai_restore_packet.sh

# Lower-level fallback commands for debugging one stage at a time:
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h bash scripts/migration/select_physeditworld_root.sh
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h bash scripts/continue_physeditworld_after_mount.sh
bash scripts/migration/run_physeditworld_phase0_preflight.sh
bash scripts/run_physeditworld_pipeline_gates.sh
```

## Safety

This verifier is CPU/IO only. It does not copy files, run rsync execute, train, rollout, evaluate videos, use GPUs, delete data, or push local_assets/checkpoints/videos.
