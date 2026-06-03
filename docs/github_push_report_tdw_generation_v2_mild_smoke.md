# GitHub Push Report: TDW Generation v2 Mild Smoke

## Repository

- Correct repo: `jh5117-debug/worldworld-phy`
- Remote URL: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Old incorrect remote avoided: `world_model_phys.git`

## Branch

- Branch: `physion-tdw-generation-v2-mild-smoke`
- Commit before adding this report: `74f0ad8b203285b1be47e41479a18a954938da41`
- Commit message: `Add mild TDW generation v2 smoke pipeline`

## Push Verification

Command used:

```bash
GIT_SSH_COMMAND='ssh -p 443' git push -u origin physion-tdw-generation-v2-mild-smoke
```

Remote verification:

```text
74f0ad8b203285b1be47e41479a18a954938da41 refs/heads/physion-tdw-generation-v2-mild-smoke
```

## Submitted Files

Committed only code/config/docs:

- `configs/cam_physgeo/tdw_generation_v2.yaml`
- `cam_physgeo/data/tdw_generation_v2/generation_config.py`
- `cam_physgeo/data/tdw_generation_v2/plan_trials.py`
- `cam_physgeo/data/tdw_generation_v2/run_tdw_trial.py`
- `docs/*.md`

## Excluded Files

Not committed:

- `local_assets/`
- generated TDW videos
- HDF5 / H5
- MP4
- NPY / NPZ
- large logs
- model weights
- checkpoints
- LoRA
- latents
- third-party raw repo

## Notes

The pushed branch fixes the mild-only camera-set blocker at the wrapper/plan level. Actual TDW generation remains blocked by TDW display/GPU routing until a GPU6/7 display is available or the user approves the existing display.

