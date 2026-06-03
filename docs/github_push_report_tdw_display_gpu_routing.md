# GitHub Push Report: TDW Display GPU Routing

## Repository

- Correct repo: `jh5117-debug/worldworld-phy`
- Remote URL: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Old incorrect remote avoided: `world_model_phys.git`

## Branch

- Branch: `physion-tdw-display-gpu-routing`
- Base branch: `physion-tdw-generation-v2-mild-smoke`
- Final commit: see remote branch head after push verification.
- Commit message: `Add TDW display GPU routing guard for generation v2`

## Scope

Committed only code/config/docs:

- `configs/cam_physgeo/tdw_generation_v2.yaml`
- `cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py`
- `scripts/31_run_tdw_generation_v2_smoke.sh`
- `docs/*.md`

## Excluded Files

Not committed:

- `local_assets/`
- generated TDW videos
- HDF5 / H5
- MP4
- NPY / NPZ
- large logs
- weights
- checkpoints
- LoRA
- latents
- third-party raw repo

## Validation

- `python3 -m compileall -q cam_physgeo`
- local display guard dry-run: blocked GPU0 as expected
- H20 display guard on `:8`: detected GPU0 and blocked before Unity
- no TDW generation launched

## Push

Push command:

```bash
GIT_SSH_COMMAND='ssh -p 443' git push -u origin physion-tdw-display-gpu-routing
```

Remote head was verified after push with:

```bash
git ls-remote --heads origin physion-tdw-display-gpu-routing
```
