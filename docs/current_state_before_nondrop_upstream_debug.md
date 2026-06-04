# Current State Before Non-Drop Upstream Debug

Date: 2026-06-04

## Summary

The TDW v2 `warmup_mild` camera gate was already passed, and drop-only generation was already stable. The remaining blocker before this round was specific to non-drop templates:

- `collision` returned code 0 but wrote no HDF5 under the project output tree.
- `roll` returned code 0 but wrote no HDF5 under the project output tree.
- `containment` returned code 0 but wrote no HDF5 under the project output tree.

Because non-drop template validation was 0/3, template-diverse 10-sample generation and 50-sample readiness were blocked.

## Existing Evidence

| Gate | Status | Evidence | Next Action |
|---|---|---|---|
| drop-only 10-sample | passed | 10/10 HDF5 validated; 10/10 LingBot conversion passed | keep as baseline only |
| warmup_mild camera set | passed | no stress/reobserve variants in plan | keep |
| non-drop command dry-run | passed | no drop-only args on `collision`, `roll`, `containment`; `--run 1` present | compare to upstream native command |
| non-drop actual | failed before this round | return code 0, no HDF5 in expected project path | audit upstream and output discovery |
| template-diverse 10 | blocked before this round | non-drop prerequisites not met | run only after non-drop 3/3 passes |
| 50/200/1k | no-go | template diversity not validated | approval required after 10-sample pass |
| DPO signal | no-go | separate gate, not run this round | keep separate |

## Why Template-Diverse 10 Could Not Run Yet

Template-diverse generation requires all requested templates to produce valid HDF5 with RGB, depth, ID, camera labels, projection/camera matrix, and object state. A return code of 0 without HDF5 is not accepted data.

This round therefore focused only on finding why non-drop templates did not write HDF5.

