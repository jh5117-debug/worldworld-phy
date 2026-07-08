# PhysEditWorld Migration Copy Plan Template

Decision: `COPY_PLAN_REVIEW_REQUIRED`

## Safety

- This is a review template, not an execute list.
- Every row is generated with `approved=false` by default.
- No data, weights, checkpoints, or local_assets were copied.
- No files were deleted.

## Outputs

- TSV: `reports/migration/approved_copy_manifest_template.tsv`

## Counts

- Rows: `800`
- Approved rows: `0`

### By Kind

- `data`: 500
- `weights`: 300

### By Copy Status

- `BLOCKED_MISSING_ON_H20`: 2
- `NEEDS_REVIEW_DIR`: 237
- `NEEDS_REVIEW_FILE`: 561

## Next Action

Review this template after the NAS and selected PhysEditWorld 50h root are visible. Only rows that are truly necessary for restore should be changed to `approved=true`; old rollouts, contact sheets, failed checkpoints, and broad `local_assets/` payloads must remain excluded.
