# GitHub Push Report: Template-Diverse TDW / DPO Signal

Date: 2026-06-03

## Branch

`physion-template-diverse-tdw-dpo-signal`

## Remote

`ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Commit

Final commit is the pushed HEAD of `physion-template-diverse-tdw-dpo-signal`.

## Commit Message

`Add template-diverse TDW gate and DPO signal sweep`

## Scope Pushed

Committed files are limited to:

- TDW generation v2 wrapper/validator/conversion code;
- `scripts/31_run_tdw_generation_v2_smoke.sh`;
- Markdown reports and plan updates.

## Excluded From Git

The following were not committed:

- `local_assets/`;
- generated HDF5/H5;
- generated MP4;
- NPY/NPZ;
- contact sheets;
- logs;
- model weights;
- latents;
- checkpoints;
- LoRA weights;
- third-party raw repositories.

## Safety Notes

- No real training was run.
- No VideoGPA `03_train.py` was run.
- No Stage1 was run.
- No 50/200/1k TDW generation was run.
- No template-diverse actual 10-sample GPU0 generation was run without approval.
