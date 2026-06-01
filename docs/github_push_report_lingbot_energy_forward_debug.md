# GitHub Push Report: LingBot Energy Forward Debug

## Branch

- Branch: `physion-lingbot-energy-forward-debug`
- Base commit before this work: `d0b6a244a41919f0446f530f4b52e20b9a31db30`
- Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Scope

Committed code and documentation only:

- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `docs/*.md`

No `local_assets/`, encoded latents, generated videos, HDF5, MP4, NPY/NPZ,
PT/PTH, safetensors, model weights, or large logs were staged.

## Validation

- `python -m compileall -q cam_physgeo`
- `PYTHONPATH=. pytest -q tests/test_reward_confidence.py`

Result: both checks passed locally before commit.

## Push Status

This report is included in the branch commit. The exact pushed commit hash is
reported in the final assistant response after `git push -u origin
physion-lingbot-energy-forward-debug` completes.
