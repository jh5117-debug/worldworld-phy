# GitHub Push Report: Reference Energy and DPO Scalar

## Branch

- Branch: `physion-reference-energy-dpo-scalar-dryrun`
- Base branch: `physion-lingbot-energy-forward-debug`
- Base commit: `f4483b1cb4bb969fea699e291432e56e009b073b`
- Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Scope

Committed code and documentation only:

- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `docs/*.md`

No `local_assets/`, encoded latents, generated videos, HDF5, MP4, NPY/NPZ,
PT/PTH, safetensors, model weights, energy tensors, TDW outputs, or large logs
were staged.

## Validation

- `python -m compileall -q cam_physgeo`
- `PYTHONPATH=. pytest -q tests/test_reward_confidence.py`

Both checks passed locally before commit.

## Runtime Smoke

Remote dry-runs completed on H20-2 using only `CUDA_VISIBLE_DEVICES=6,7`:

- `reference_energy_dryrun`: passed.
- `dpo_scalar_loss_dryrun`: passed.

No training, backward, optimizer, VideoGPA `03_train.py`, Stage1, rollout, or
reward calibration was run.

## Push Status

This report is included in the branch commit. The exact pushed commit hash is
reported in the final assistant response after push completes.
