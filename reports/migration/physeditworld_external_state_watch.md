# PhysEditWorld External State Watch

Decision: `PHYS_EDITWORLD_EXTERNAL_STATE_WAITING_FOR_NAS`

## Rows

- `nas_target`: `BLOCKED`
  - detail: /mnt/workspace/hj/nas_hj exists=False
  - next: mount or expose NAS target
- `physeditworld_roots_env`: `BLOCKED`
  - detail: PHYS_EDITWORLD_ROOTS is unset
  - next: export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root
- `external_root_handoff`: `PASS`
  - detail: reports/migration/physeditworld_external_root_handoff_packet.json: PHYS_EDITWORLD_EXTERNAL_ROOT_HANDOFF_WAITING_FOR_FILLED_TEMPLATE
  - next: fill reports/migration/physeditworld_root_submission_template.tsv
- `root_onboarding`: `PASS`
  - detail: reports/migration/physeditworld_root_onboarding_sequence.json: PHYS_EDITWORLD_ROOT_ONBOARDING_WAITING_FOR_FILLED_TEMPLATE
  - next: continue
- `root_validation`: `PASS`
  - detail: reports/migration/physeditworld_root_submission_validation.json: PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE
  - next: continue
- `root_evidence_samples`: `PASS`
  - detail: reports/migration/physeditworld_root_evidence_samples.json: PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE
  - next: continue
- `root_selection`: `BLOCKED`
  - detail: reports/migration/physeditworld_selected_root_status.json: PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT
  - next: fix the blocker recorded in the report
- `root_schema_probe`: `BLOCKED`
  - detail: reports/migration/physeditworld_root_schema_probe.json: PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT
  - next: run scripts/migration/probe_physeditworld_root_schema.sh after root lock
- `pai_handoff`: `BLOCKED`
  - detail: reports/migration/pai_handoff_status.json: PAI_HANDOFF_BLOCKED_NAS_OR_ROOT
  - next: fix the blocker recorded in the report
- `requirement_matrix`: `BLOCKED`
  - detail: reports/physeditworld_50h/requirement_matrix.json: PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS
  - next: fix the blocker recorded in the report

## Safety

This watcher is one-shot CPU/IO only. It reads environment/path visibility plus existing JSON reports. It does not copy files, delete files, use GPUs, train, rollout, evaluate videos, run DPO, or select/lock a root.
