# PhysEditWorld Root Onboarding Sequence

Decision: `PHYS_EDITWORLD_ROOT_ONBOARDING_WAITING_FOR_FILLED_TEMPLATE`

## Steps

- `write_template_if_missing`: `PASS` / `PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY`
  - report: `reports/migration/physeditworld_root_submission_template.json`
  - detail: template TSV already exists; not overwritten
  - next: fill TSV if still placeholder
- `validate_submission`: `PASS` / `PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE`
  - report: `reports/migration/physeditworld_root_submission_validation.json`
  - detail: {"decision": "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE", "rows": 1}
  - next: fill reports/migration/physeditworld_root_submission_template.tsv with the selected 50h root and bounded evidence globs
- `sample_evidence`: `PASS` / `PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE`
  - report: `reports/migration/physeditworld_root_evidence_samples.json`
  - detail: {"decision": "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE", "samples": 1}
  - next: fill reports/migration/physeditworld_root_submission_template.tsv with the selected 50h root and bounded evidence globs

## Safe Resume Commands

```bash
cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys
bash scripts/migration/run_physeditworld_root_onboarding_sequence.sh
export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root
bash scripts/migration/select_physeditworld_root.sh
bash scripts/migration/probe_physeditworld_root_schema.sh
bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh
```

## Safety

This sequence is CPU/IO only. It does not overwrite an existing filled TSV, copy files, delete files, approve migration rows, select/lock a root, use GPUs, train, rollout, evaluate videos, or run DPO.
