# GitHub Push Report: TDW 10-Sample Warmup Smoke

Generated: 2026-06-04

## Remote

- Correct repo: `jh5117-debug/worldworld-phy`
- Remote URL: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Old wrong repo avoided: `world_model_phys.git`

## Branch

- Branch: `physion-tdw-10sample-warmup-smoke`
- Commit: branch tip pushed successfully. Use `git ls-remote origin refs/heads/physion-tdw-10sample-warmup-smoke` for the exact SHA.
- Commit message: `Run approved TDW 10-sample warmup smoke`

## Scope

Committed only markdown reports and planning updates.

Not committed:

- `local_assets/`
- generated HDF5 / MP4
- NPY / NPZ
- contact sheets
- logs
- weights
- latents
- checkpoints
- LoRA

## Summary

The branch records:

- approved GPU0-bound `DISPLAY=:8` 10-sample TDW `warmup_mild` smoke;
- 10/10 HDF5 validation passed;
- 10/10 LingBot cam-only conversion/probe passed;
- 50-sample approval request prepared but not executed;
- no training, DPO, VideoGPA `03_train.py`, Stage1, reward calibration, or 50/200/1k generation.
