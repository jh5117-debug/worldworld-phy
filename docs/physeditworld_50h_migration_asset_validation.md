# PhysEditWorld 50h Migration Asset Validation

This checker validates the H20 to PAI/NAS migration manifests before any copy is attempted.

It is intentionally read-only:

- It does not copy data or weights.
- It does not delete data, checkpoints, or weights.
- It does not recursively hash large directories.
- It does not include `local_assets/` as a migration payload.

Run:

```bash
bash scripts/migration/validate_physeditworld_migration_assets.sh
```

Expected outputs:

- `reports/migration/migration_asset_validation.csv`
- `reports/migration/migration_asset_validation.json`
- `reports/migration/migration_asset_validation_summary.md`

Current expected blocker on H20 is that `/mnt/workspace/hj/nas_hj` is not mounted or visible. In that case the correct decision is `MIGRATION_ASSET_VALIDATION_NAS_BLOCKED`; this is not a copy failure and should not be papered over by local-only paths.
