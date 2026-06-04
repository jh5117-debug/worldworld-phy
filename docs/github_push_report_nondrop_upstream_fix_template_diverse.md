# GitHub Push Report: Non-Drop Upstream Fix Template-Diverse

Date: 2026-06-04

## Branch

`physion-nondrop-upstream-fix-template-diverse`

## Remote

`ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Commit Message

`Fix non-drop TDW template generation and validate template-diverse smoke`

## Scope

Committed code and docs only:

- TDW v2 non-drop wrapper fixes;
- manifest-aware LingBot conversion fix;
- `imageio` fallback for MP4 probing;
- non-drop/template-diverse validation reports;
- 50-sample approval request.

Excluded:

- `local_assets/`
- generated HDF5 / MP4 / NPY / NPZ
- contact sheets
- logs
- weights / latents / checkpoints / LoRA

## Validation

- local `compileall` passed for modified Python files;
- remote non-drop 3-sample smoke passed;
- remote template-diverse 10-sample smoke passed;
- remote LingBot cam-only conversion passed.

## Push Status

Pushed to `origin` after commit.

