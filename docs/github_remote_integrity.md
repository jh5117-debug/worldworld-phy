# GitHub Remote Integrity

## Correct Repository

- Correct repo: `jh5117-debug/worldworld-phy`
- Fixed remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Old incorrect remote: `world_model_phys.git`

The local scratch worktree had `origin` pointing at the old `world_model_phys.git`
remote during part of the DPO smoke sequence. That remote is not the
user-visible GitHub repository shown in the GitHub branch page. Future pushes
must target `jh5117-debug/worldworld-phy`.

## Remote Repair

The working remote was corrected with:

```bash
git remote set-url origin ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git
```

Pushes should use `origin` only after this check passes:

```bash
git remote -v
git ls-remote --heads origin
```

The helper script below performs the same check and fails if `origin` points at
the old repository:

```bash
scripts/check_github_remote_integrity.sh
```

## Confirmed Branches

The following branches were confirmed on `jh5117-debug/worldworld-phy`:

- `physion-dpo-lora-optimizer-step-dryrun`
- `physion-dpo-1pair-overfit-miniloop`
- `physion-dpo-fixed-noise-diagnostic`
- `physion-dpo-signal-sensitivity`

## Required Push Checklist

Before any future push:

1. Run `git remote -v`.
2. Confirm both fetch and push URLs are
   `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`.
3. Run `git ls-remote --heads origin`.
4. Confirm the target branch appears under `refs/heads/` after pushing.
5. Do not push to any remote containing `world_model_phys.git`.

No `local_assets/`, videos, latents, weights, HDF5, NPY/NPZ, PT/PTH,
safetensors, checkpoints, or generated smoke outputs should be committed or
pushed.
