# TDW Generation v2 Template-Diverse 10 Retry Report

Date: 2026-06-04

## Status

Skipped.

The template-diverse 10 retry was conditional on the non-drop 3-sample smoke passing for:

- `collision`;
- `roll`;
- `containment`.

That gate did not pass because validation found no HDF5 files for the non-drop smoke.

## Planned Distribution If Allowed

| Template | Count |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

## Reason for Skip

The non-drop actual smoke revealed a wrapper execution blocker: the upstream runner needs `--run 1` to actually write HDF5. This has been fixed in code, but the approved actual TDW run was already consumed.

## Gate Decision

Template-diverse 10 retry: **not run**.

Next action: request approval to rerun non-drop 3-sample smoke, then template-diverse 10 only if non-drop validation passes.

