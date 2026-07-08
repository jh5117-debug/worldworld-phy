# PhysEditWorld Migration Asset Validation

Decision: `MIGRATION_ASSET_VALIDATION_NAS_BLOCKED`

## Safety

- No files were copied.
- No files, checkpoints, weights, or data were deleted.
- Directories and large files were not recursively hashed.
- `local_assets/` is not included as a migration payload.

## NAS Target

- Path: `/mnt/workspace/hj/nas_hj`
- Status: `BLOCKED_MISSING`
- Exists/readable/writable: `False` / `False` / `False`
- Free bytes: `unknown`

## Execute Guard

- Path: `scripts/migration/rsync_h20_to_pai_execute.sh`
- Status: `PASS`
- Requires `MIGRATION_APPROVED=1`: `True`

## Manifest Summary

- Rows: `800`
- Present file bytes counted: `5.97 GB`

### By Kind

- `data`: 500
- `weights`: 300

### By Validation Status

- `DIR_PRESENT_NOT_HASHED`: 237
- `FILE_PRESENT_NO_SHA256`: 4
- `FILE_PRESENT_SHA256_OK`: 557
- `MISSING_ON_DISK`: 2

## Next Action

Mount or expose `/mnt/workspace/hj/nas_hj`, then rerun `bash scripts/migration/validate_physeditworld_migration_assets.sh` before any execute migration.
