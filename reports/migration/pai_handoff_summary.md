# PhysEditWorld PAI Handoff Verification

Decision: `PAI_HANDOFF_BLOCKED_NAS_OR_ROOT`

## Status Counts

- `BLOCKED`: 4
- `PASS`: 5

## Checks

- `git_branch`: `PASS`
  - detail: branch=physion-only-local-assets-videogpa-smoke
- `git_head`: `PASS`
  - detail: cb71dc2
- `forbidden_staged_files`: `PASS`
  - detail: none
- `required_handoff_files`: `PASS`
  - detail: missing=0 total=15
- `phase0_report_artifacts`: `PASS`
  - detail: missing=0 total=8 decisions={"reports/migration/approved_copy_status.json": "APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS", "reports/migration/migration_asset_validation.json": "MIGRATION_ASSET_VALIDATION_NAS_BLOCKED", "reports/migration/phase0_preflight_status.json": "PHYS_EDITWORLD_PHASE0_BLOCKED_AT_READINESS", "reports/migration/physeditworld_pai_readiness.json": "PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED", "reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json": "PIPELINE_BLOCKED_AT_READINESS", "reports/physeditworld_50h/requirement_matrix.json": "PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS"}
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
bash scripts/migration/run_physeditworld_phase0_preflight.sh
bash scripts/run_physeditworld_pipeline_gates.sh
python3 -m cam_physgeo.orchestration.physeditworld_requirement_matrix
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h bash scripts/continue_physeditworld_after_mount.sh
```

## Safety

This verifier is CPU/IO only. It does not copy files, run rsync execute, train, rollout, evaluate videos, use GPUs, delete data, or push local_assets/checkpoints/videos.
