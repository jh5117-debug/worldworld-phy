# Migration Size Summary

Decision: `MIGRATION_SIZE_SUMMARY_NO_APPROVED_ROWS`

## Candidate Required Assets

- Manifest rows: `800`
- Present file bytes counted: `6415095518` (5.97 GB)
- Directory rows pending recursive sizing: `237`
- Missing rows: `2`

This report intentionally does not run recursive `du` and does not copy or delete any file. Directory rows remain pending until an approved migration payload is selected.

## Approved Copy Payload

- Approved-copy status decision: `APPROVED_COPY_BLOCKED_NO_APPROVED_ROWS`
- Approved rows: `0`
- Approved present file bytes: `0` (0.00 B)
- Approved directory rows pending recursive sizing: `0`
- Approved missing rows: `0`

## NAS Target

- Path: `/mnt/workspace/hj/nas_hj`
- Status: `BLOCKED_MISSING`
- Exists: `False`; is_dir: `False`; readable: `False`; writable: `False`
- Free bytes: `None` (unknown)

## Manifest Breakdown

| kind | rows | present files | present dirs | missing | present file bytes |
|---|---:|---:|---:|---:|---:|
| weights | 300 | 180 | 116 | 2 | 3435967937 |
| data | 500 | 379 | 121 | 0 | 2979127581 |

## Safety

- Copied files: `False`
- Deleted files: `False`
- Recursive directory sizing: `False`
- local_assets included by policy: `False`
