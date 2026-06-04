# GitHub Push Report: Template-Diverse TDW / DPO Signal Run

Date: 2026-06-04

## Branch

`physion-template-diverse-tdw-dpo-signal-run`

## Remote

`ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Commit Message

`Run template-diverse TDW smoke and DPO signal gate`

## Scope

This branch records:

- the approved template-diverse TDW 10-sample attempt outcome;
- the exact non-drop upstream argument blocker;
- the fix that only passes drop-specific args to `template == "drop"`;
- the partial DPO signal fast sweep result;
- the 5-pair no-go decision;
- the 50-sample no-go / approval requirement.

## Not Committed

The following were intentionally not committed:

- `local_assets/`;
- generated HDF5/H5;
- generated MP4;
- NPY/NPZ;
- contact sheets;
- large logs;
- weights;
- checkpoints;
- LoRA weights;
- latents;
- third-party raw repositories.

## Safety

- No real training was run.
- No VideoGPA `03_train.py` was run.
- No Stage1 was run.
- No 50/200/1k TDW generation was run.
- No 5-pair tiny overfit was run.
- No LoRA/checkpoint was saved.

