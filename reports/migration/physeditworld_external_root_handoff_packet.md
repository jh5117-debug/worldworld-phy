# PhysEditWorld External Root Handoff Packet

Decision: `PHYS_EDITWORLD_EXTERNAL_ROOT_HANDOFF_WAITING_FOR_FILLED_TEMPLATE`

## Operator Summary

The onboarding toolchain is ready, but the selected-root TSV still contains placeholders. Fill the TSV with the real PhysEditWorld selected 50h root plus bounded action/camera/intrinsics/gravity/replay/video evidence globs.

## Report Decisions

- `root_template`: `PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY`
  - path: `reports/migration/physeditworld_root_submission_template.json`
  - next: send TSV to data owner or fill it with selected-root evidence
- `root_validation`: `PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE`
  - path: `reports/migration/physeditworld_root_submission_validation.json`
  - next: fill the selected-root submission TSV
- `root_evidence_samples`: `PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE`
  - path: `reports/migration/physeditworld_root_evidence_samples.json`
  - next: fill the selected-root submission TSV
- `root_onboarding`: `PHYS_EDITWORLD_ROOT_ONBOARDING_WAITING_FOR_FILLED_TEMPLATE`
  - path: `reports/migration/physeditworld_root_onboarding_sequence.json`
  - next: fill reports/migration/physeditworld_root_submission_template.tsv with selected 50h root and evidence globs
- `external_state_watch`: `PHYS_EDITWORLD_EXTERNAL_STATE_WAITING_FOR_NAS`
  - path: `reports/migration/physeditworld_external_state_watch.json`
  - next: mount or expose /mnt/workspace/hj/nas_hj before PAI handoff
- `root_candidates`: `PHYS_EDITWORLD_ROOT_CANDIDATES_NONE_STRONG`
  - path: `reports/migration/physeditworld_root_candidates_ranked.json`
  - next: continue to the next root onboarding gate
- `root_schema_probe`: `PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT`
  - path: `reports/migration/physeditworld_root_schema_probe.json`
  - next: fill the selected-root submission TSV
- `root_selection`: `PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT`
  - path: `reports/migration/physeditworld_selected_root_status.json`
  - next: fix the blocker recorded in the report
- `requirement_matrix`: `PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS`
  - path: `reports/physeditworld_50h/requirement_matrix.json`
  - next: fix the blocker recorded in the report
- `completion_audit`: `PHYS_EDITWORLD_OBJECTIVE_INCOMPLETE_AT_PHASE0_MIGRATION`
  - path: `reports/physeditworld_50h/completion_audit/physeditworld_completion_matrix.json`
  - next: continue to the next root onboarding gate

## Commands

```bash
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys
bash scripts/migration/run_physeditworld_root_onboarding_sequence.sh
# Fill reports/migration/physeditworld_root_submission_template.tsv if still waiting.
export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root
bash scripts/migration/select_physeditworld_root.sh
bash scripts/migration/probe_physeditworld_root_schema.sh
bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh
```

## Safety

This packet is CPU/IO only. It reads existing JSON reports and writes a lightweight operator packet. It does not copy files, delete files, use GPUs, train, rollout, run DPO, or select/lock a root.
