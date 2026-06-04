# TDW Generation v2 Template-Diverse 10 `run1` Report

Date: 2026-06-04

## Status

Skipped.

The template-diverse 10 retry was conditional on the non-drop 3-sample `--run 1` smoke validating 3/3. That gate failed with `0/3` accepted HDF5 files.

## Planned Distribution

| Template | Count |
|---|---:|
| drop | 3 |
| collision | 3 |
| roll | 2 |
| containment | 2 |

## Reason for Skip

The non-drop templates returned code 0 but wrote no HDF5, so there is no evidence that `collision`, `roll`, or `containment` work in the current wrapper/upstream invocation.

## Gate Decision

Template-diverse 10 `run1`: **not run / dependency failed**.

Do not request 50 until a non-drop smoke and template-diverse 10 both pass.

