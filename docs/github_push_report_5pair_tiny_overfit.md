# GitHub Push Report: 5-Pair Tiny DPO Overfit Gate

## Branch

- Branch: `physion-dpo-5pair-tiny-overfit`
- Correct repo: `jh5117-debug/worldworld-phy`
- Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Commit message: `Add 5-pair tiny DPO overfit smoke`

## Result

The 5-pair tiny overfit run was skipped by gate, so this branch commits the
decision report and prior-art review rather than experiment outputs.

## Scope Committed

Committed lightweight docs only:

- `docs/prior_art_5pair_tiny_overfit_review.md`
- `docs/final_report_5pair_tiny_overfit.md`
- `docs/github_push_report_5pair_tiny_overfit.md`
- `docs/stage2_videogpa_dpo_plan.md`
- `docs/physion_tdw_large_scale_generation_plan.md`

Not committed:

- `local_assets/`
- encoded latents
- generated videos
- optimizer outputs
- gradient tensors
- checkpoints
- saved LoRA
- HDF5/MP4/NPY/NPZ/PT/PTH/safetensors
- large logs
- third-party raw repos

## Remote Integrity

Verified before push:

```bash
git remote -v
git ls-remote --heads origin
```

Do not push to `world_model_phys.git`.
