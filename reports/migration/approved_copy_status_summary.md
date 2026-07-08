# Approved Migration Copy Status

Decision: `APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS`

## Safety

- Execute mode: `False`
- Only rows with `approved=true` are considered.
- `local_assets/` payloads are rejected.
- No unknown process is killed and no source file is deleted.

## Counts

- Approved rows considered: `0`

### By Copy Status

- none

## Next Action

Review `reports/migration/approved_copy_manifest_template.tsv` and explicitly mark only required restore assets as `approved=true` after NAS/data visibility is confirmed.
