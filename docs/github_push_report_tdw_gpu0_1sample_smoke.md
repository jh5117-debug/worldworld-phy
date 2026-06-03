# GitHub Push Report: TDW GPU0 1-Sample Smoke

## Repository

- Correct repo: `jh5117-debug/worldworld-phy`
- Remote URL: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Old incorrect remote avoided: `world_model_phys.git`

## Branch

- Branch: `physion-tdw-gpu0-1sample-smoke`
- Base branch: `physion-tdw-display-gpu-routing`
- Commit message: `Run approved GPU0 one-sample TDW warmup smoke`

## Scope

Committed only code/docs:

- `cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py`
- `docs/*.md`

## Excluded Files

Not committed:

- `local_assets/`
- generated HDF5 / H5
- generated MP4
- NPY / NPZ
- contact sheets
- large logs
- weights
- latents
- checkpoints
- LoRA
- third-party raw repo

## Result

The user approved GPU0 / `DISPLAY=:8` for exactly one `warmup_mild` TDW smoke. The run failed before TDW/Unity scene generation due runtime-wrapper startup issues, so no HDF5/MP4/contact sheet exists. No 10/50 stage was run.

## Validation

- `python3 -m compileall -q cam_physgeo`
- `git diff --check`
- H20 validation after failed run: HDF5 count `0`, suitable-for-warmup `0`

## Push Verification

After push, verify:

```bash
git ls-remote --heads origin physion-tdw-gpu0-1sample-smoke
```

