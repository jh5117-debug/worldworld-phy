# PhysEditWorld Phase 0 Migration Preflight

Decision: `PHYS_EDITWORLD_PHASE0_BLOCKED_AT_READINESS`

## Steps

- `empty_manifest_init`: `PASS` / `PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT`
  - evidence: `reports/physeditworld_50h/manifest_init/empty_manifest_init.json`
  - command: `bash scripts/migration/init_physeditworld_empty_manifests.sh`
- `physeditworld_pai_readiness`: `BLOCKED` / `PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED`
  - evidence: `reports/migration/physeditworld_pai_readiness.json`
  - command: `bash scripts/migration/check_physeditworld_pai_readiness.sh`
- `physeditworld_root_candidates_ranked`: `BLOCKED` / `PHYS_EDITWORLD_ROOT_CANDIDATES_NONE_STRONG`
  - evidence: `reports/migration/physeditworld_root_candidates_ranked.json`
  - command: `bash scripts/migration/rank_physeditworld_root_candidates.sh`
- `physeditworld_selected_root_status`: `BLOCKED` / `PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT`
  - evidence: `reports/migration/physeditworld_selected_root_status.json`
  - command: `bash scripts/migration/select_physeditworld_root.sh`
- `migration_asset_validation`: `BLOCKED` / `MIGRATION_ASSET_VALIDATION_NAS_BLOCKED`
  - evidence: `reports/migration/migration_asset_validation.json`
  - command: `bash scripts/migration/validate_physeditworld_migration_assets.sh`
- `approved_copy_manifest_template`: `REVIEW_REQUIRED` / `COPY_PLAN_REVIEW_REQUIRED`
  - evidence: `reports/migration/approved_copy_manifest_template.json`
  - command: `bash scripts/migration/build_physeditworld_migration_copy_plan.sh`
- `approved_copy_status`: `BLOCKED` / `APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS`
  - evidence: `reports/migration/approved_copy_status.json`
  - command: `bash scripts/migration/run_approved_migration_copy.sh`
- `requirement_matrix`: `BLOCKED` / `PHYS_EDIT_WORLD_PIPELINE_BLOCKED_AT_MIGRATION_READINESS`
  - evidence: `reports/physeditworld_50h/requirement_matrix.json`
  - command: `python3 -m cam_physgeo.orchestration.physeditworld_requirement_matrix`
- `pipeline_gate_status`: `BLOCKED` / `PIPELINE_BLOCKED_AT_READINESS`
  - evidence: `reports/physeditworld_50h/pipeline_gate/pipeline_gate_status.json`
  - command: `python3 -m cam_physgeo.orchestration.physeditworld_pipeline_gate`

## Safety

- This preflight does not run rsync execute.
- It does not pass `--execute` to the approved-copy tool.
- It does not copy data, weights, checkpoints, videos, or local_assets.
- It does not delete files and does not use GPUs.
