# GitHub Push Report: TDW v5 200 Stage A Warmup Pilot

Date: 2026-06-09

Branch:

`physion-tdw-v5-200-stageA-warmup-pilot`

Commit message:

`Run Stage A TDW v5 200 high-noise warmup pilot`

Push target:

`origin physion-tdw-v5-200-stageA-warmup-pilot`

Remote:

`ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`

## Submitted Scope

Included:

- `cam_physgeo/training/lingbot_warmup_smoke.py`
- `docs/*.md`

Excluded:

- `local_assets/`
- train metrics under `local_assets`
- checkpoints
- LoRA files
- optimizer states
- generated videos
- HDF5 / MP4 / NPY
- logs large
- weights
- latents
- third-party raw repos

## Gate Summary

Stage A high-noise warmup pilot passed as a 20-step metrics-only run:

- train loss finite;
- validation loss finite;
- runtime LoRA changed;
- sampled base tensors unchanged;
- no checkpoint, LoRA, or optimizer state saved.
